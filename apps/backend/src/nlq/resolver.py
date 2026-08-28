import uuid
from dataclasses import dataclass

from src.nlq.models import (
    DatasetSummary,
    PlaceCandidate,
    ProjectCatalogue,
    SpatialIntent,
)
from src.unit_of_work import UnitOfWork


class ResolutionFailure(Exception):
    """A name in the intent does not exist in this project.

    Carries a message written for the person who asked the question, because it
    is shown to them verbatim.
    """


@dataclass(frozen=True)
class ResolvedQuery:
    """An intent with every name replaced by a real identifier.

    Nothing reaches the spatial engine until it is expressed in these terms, and
    every field here was produced by a database lookup rather than by the model.
    """

    operation: str
    dataset_id: uuid.UUID
    place: PlaceCandidate
    category: str | None = None
    radius_meters: float | None = None
    target_dataset_id: uuid.UUID | None = None


class SpatialResolver:
    """Turns names into identifiers, and refuses when it cannot.

    This is the security boundary. The interpreter can propose any string it
    likes; nothing here trusts it. A dataset, category or place that does not
    exist in the project fails closed with an explanation, and a place that
    matches more than one feature is reported as ambiguous rather than picked.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def load_catalogue(self, project_id: uuid.UUID) -> ProjectCatalogue:
        rows = await self._uow.dataset_features.summarise_project(project_id)
        return ProjectCatalogue(
            datasets=[
                DatasetSummary(
                    name=row["dataset_name"],
                    feature_count=row["feature_count"],
                    categories=sorted(row["categories"] or []),
                )
                for row in rows
            ]
        )

    async def find_places(
        self, project_id: uuid.UUID, name: str
    ) -> list[PlaceCandidate]:
        rows = await self._uow.dataset_features.find_by_name(project_id, name)
        return [
            PlaceCandidate(
                feature_id=row["feature_id"],
                feature_name=row["feature_name"],
                dataset_id=row["dataset_id"],
                dataset_name=row["dataset_name"],
                category=row["category"],
                geometry_type=row["geometry_type"],
                lon=row["lon"],
                lat=row["lat"],
            )
            for row in rows
        ]

    async def _dataset_id_by_name(self, project_id: uuid.UUID, name: str) -> uuid.UUID:
        datasets = await self._uow.datasets.find_by_project(project_id)
        for dataset in datasets:
            if dataset.name.casefold() == name.casefold():
                return dataset.id
        known = ", ".join(sorted(d.name for d in datasets)) or "none"
        raise ResolutionFailure(
            f"There is no dataset called '{name}' in this project. "
            f"Available datasets: {known}."
        )

    def _validate_category(self, catalogue: ProjectCatalogue, category: str) -> str:
        available = catalogue.category_values()
        for value in available:
            if value.casefold() == category.casefold():
                return value
        known = ", ".join(sorted(available)) or "none"
        raise ResolutionFailure(
            f"There is no category called '{category}' in this project. "
            f"Available categories: {known}."
        )

    async def resolve(
        self,
        project_id: uuid.UUID,
        intent: SpatialIntent,
        catalogue: ProjectCatalogue,
        place: PlaceCandidate,
    ) -> ResolvedQuery:
        """Bind a single already-disambiguated place into an executable query."""
        category = (
            self._validate_category(catalogue, intent.target_category)
            if intent.target_category
            else None
        )

        # Which dataset do we search? An explicitly named one when the user
        # named it, otherwise the dataset the reference place itself lives in -
        # the primitives each operate within one dataset.
        if intent.operation == "intersects":
            if not intent.target_dataset:
                raise ResolutionFailure(
                    "This comparison needs a dataset to test against."
                )
            target_dataset_id = await self._dataset_id_by_name(
                project_id, intent.target_dataset
            )
            return ResolvedQuery(
                operation=intent.operation,
                dataset_id=place.dataset_id,
                place=place,
                category=category,
                target_dataset_id=target_dataset_id,
            )

        dataset_id = (
            await self._dataset_id_by_name(project_id, intent.target_dataset)
            if intent.target_dataset
            else place.dataset_id
        )

        return ResolvedQuery(
            operation=intent.operation,
            dataset_id=dataset_id,
            place=place,
            category=category,
            radius_meters=intent.distance_meters,
        )
