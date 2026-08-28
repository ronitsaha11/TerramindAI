import logging
import uuid
from typing import Any

from src.nlq.exceptions import InterpretationError
from src.nlq.interpreter import NLQInterpreter
from src.nlq.models import NaturalQueryResult, PlaceCandidate
from src.nlq.resolver import ResolutionFailure, ResolvedQuery, SpatialResolver
from src.services.dataset_service import DatasetService
from src.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


def _format_distance(metres: float) -> str:
    if metres >= 1000:
        return f"{metres / 1000:g} km"
    return f"{metres:g} m"


def _pluralise(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


class NaturalQueryService:
    """Runs the natural-language pipeline over the existing spatial engine.

    The division of labour is deliberate and total: the interpreter decides
    *what was asked*, this service decides *whether that is answerable*, and the
    existing DatasetService computes the geography. No SQL is written here, and
    no number in the reply is produced by a language model - counts come from
    the engine's own result.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        dataset_service: DatasetService,
        interpreter: NLQInterpreter,
    ) -> None:
        self._uow = uow
        self._dataset_service = dataset_service
        self._interpreter = interpreter
        self._resolver = SpatialResolver(uow)

    async def answer(self, project_id: uuid.UUID, query: str) -> NaturalQueryResult:
        # The catalogue is read and the connection released before the network
        # call, so a slow interpreter never holds a database session open.
        async with self._uow:
            catalogue = await self._resolver.load_catalogue(project_id)

        if not catalogue.datasets:
            return NaturalQueryResult(
                status="unresolved",
                query=query,
                answer=(
                    "This project has no datasets yet, so there is nothing to "
                    "search. Upload a dataset first."
                ),
            )

        intent = await self._interpreter.interpret(query, catalogue)
        if not intent.reference_place:
            raise InterpretationError("The interpreter returned no place to search.")

        async with self._uow:
            places = await self._resolver.find_places(
                project_id, intent.reference_place
            )

            if not places:
                return NaturalQueryResult(
                    status="unresolved",
                    query=query,
                    interpretation=intent,
                    answer=(
                        f"Nothing in this project is called '{intent.reference_place}'."
                    ),
                )

            if len(places) > 1:
                return self._ambiguous(query, intent, places)

            try:
                resolved = await self._resolver.resolve(
                    project_id, intent, catalogue, places[0]
                )
            except ResolutionFailure as exc:
                return NaturalQueryResult(
                    status="unresolved",
                    query=query,
                    interpretation=intent,
                    answer=str(exc),
                )

        geojson = await self._dispatch(project_id, resolved)
        features = self._filter_by_category(
            geojson.get("features", []), resolved.category
        )

        return NaturalQueryResult(
            status="ok",
            query=query,
            interpretation=intent,
            answer=self._describe(resolved, len(features)),
            result={"type": "FeatureCollection", "features": features},
            focus={"lon": resolved.place.lon, "lat": resolved.place.lat},
        )

    def _ambiguous(
        self, query: str, intent: Any, places: list[PlaceCandidate]
    ) -> NaturalQueryResult:
        names = ", ".join(f"'{p.feature_name}'" for p in places)
        return NaturalQueryResult(
            status="ambiguous",
            query=query,
            interpretation=intent,
            answer=(
                f"'{intent.reference_place}' matches {len(places)} places in this "
                f"project: {names}. Which one did you mean?"
            ),
            candidates=places,
        )

    async def _dispatch(
        self, project_id: uuid.UUID, resolved: ResolvedQuery
    ) -> dict[str, Any]:
        """Call the existing, verified primitive for this operation.

        A closed match over three known operations - there is no path here that
        builds a query from model output.
        """
        if resolved.operation == "nearby":
            if resolved.radius_meters is None:
                raise InterpretationError("A radius is required for this query.")
            return await self._dataset_service.query_nearby(
                project_id=project_id,
                dataset_id=resolved.dataset_id,
                lon=resolved.place.lon,
                lat=resolved.place.lat,
                radius_meters=resolved.radius_meters,
            )

        if resolved.operation == "contains":
            return await self._dataset_service.query_contains(
                project_id=project_id,
                dataset_id=resolved.dataset_id,
                feature_id=resolved.place.feature_id,
            )

        if resolved.operation == "intersects":
            if resolved.target_dataset_id is None:
                raise InterpretationError("A dataset to compare against is required.")
            return await self._dataset_service.query_intersects(
                project_id=project_id,
                dataset_id=resolved.dataset_id,
                feature_id=resolved.place.feature_id,
                target_dataset_id=resolved.target_dataset_id,
            )

        raise InterpretationError(f"Unsupported operation '{resolved.operation}'.")

    @staticmethod
    def _filter_by_category(
        features: list[dict[str, Any]], category: str | None
    ) -> list[dict[str, Any]]:
        """Narrow engine output to one category.

        The nearby/contains/intersects primitives are purely geometric - they
        return everything that satisfies the predicate. "Hospitals within 2 km"
        is a geometric question plus an attribute filter, and the filter belongs
        here rather than in the verified SQL.
        """
        if not category:
            return features
        wanted = category.casefold()
        return [
            feature
            for feature in features
            if str((feature.get("properties") or {}).get("category", "")).casefold()
            == wanted
        ]

    @staticmethod
    def _describe(resolved: ResolvedQuery, count: int) -> str:
        noun = resolved.category or "feature"
        subject = _pluralise(count, noun)
        place = resolved.place.feature_name

        if resolved.operation == "nearby" and resolved.radius_meters is not None:
            return (
                f"Found {subject} within {_format_distance(resolved.radius_meters)} "
                f"of {place}."
            )
        if resolved.operation == "contains":
            return f"Found {subject} inside {place}."
        return f"Found {subject} overlapping {place}."
