"""Test doubles for the natural-language pipeline.

Mirrors the real Bangalore data closely enough that the tests exercise the
cases that actually occur - in particular "Lalbagh" matching three different
features. Not named test_* so pytest does not collect it.
"""

import uuid
from types import SimpleNamespace
from typing import Any

from src.nlq.models import ProjectCatalogue, SpatialIntent

PROJECT_ID = uuid.UUID("237f0d73-d434-47cd-9381-1c833a7e5751")
BANGALORE_ID = uuid.UUID("86366ad9-9947-4096-a7db-44be16050193")
TEST_DATA_ID = uuid.UUID("a18515d4-85c1-443e-94e0-aa601e5b98d9")

STATION_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
NURSING_HOME_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
GARDENS_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")

# The three real features that make "Lalbagh" ambiguous.
FEATURE_ROWS: list[dict[str, Any]] = [
    {
        "feature_id": STATION_ID,
        "feature_name": "Lalbagh",
        "dataset_id": BANGALORE_ID,
        "dataset_name": "bangalore osm",
        "category": "station",
        "geometry_type": "ST_Point",
        "lon": 77.5800,
        "lat": 12.9465,
    },
    {
        "feature_id": NURSING_HOME_ID,
        "feature_name": "Lalbagh Nursing Home",
        "dataset_id": BANGALORE_ID,
        "dataset_name": "bangalore osm",
        "category": "hospital",
        "geometry_type": "ST_Point",
        "lon": 77.5862,
        "lat": 12.9452,
    },
    {
        "feature_id": GARDENS_ID,
        "feature_name": "Lalbagh Botanical Gardens",
        "dataset_id": BANGALORE_ID,
        "dataset_name": "bangalore osm",
        "category": "park",
        "geometry_type": "ST_Polygon",
        "lon": 77.5856,
        "lat": 12.9486,
    },
    {
        "feature_id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "feature_name": "Cubbon Park",
        "dataset_id": BANGALORE_ID,
        "dataset_name": "bangalore osm",
        "category": "park",
        "geometry_type": "ST_Polygon",
        "lon": 77.5946,
        "lat": 12.9763,
    },
]

SUMMARY_ROWS: list[dict[str, Any]] = [
    {
        "dataset_name": "bangalore osm",
        "feature_count": 1188,
        "categories": ["hospital", "park", "station"],
    },
    {"dataset_name": "test data", "feature_count": 3, "categories": []},
]

DATASETS = [
    SimpleNamespace(id=BANGALORE_ID, name="bangalore osm"),
    SimpleNamespace(id=TEST_DATA_ID, name="test data"),
]


def feature(name: str, category: str) -> dict[str, Any]:
    """A GeoJSON feature as the spatial engine returns it."""
    return {
        "type": "Feature",
        "id": str(uuid.uuid4()),
        "geometry": {"type": "Point", "coordinates": [77.58, 12.94]},
        "properties": {"name": name, "category": category},
    }


class FakeFeatureRepo:
    def __init__(
        self,
        rows: list[dict[str, Any]] | None = None,
        summary: list[dict[str, Any]] | None = None,
    ) -> None:
        self._rows = FEATURE_ROWS if rows is None else rows
        self._summary = SUMMARY_ROWS if summary is None else summary

    async def find_by_name(
        self, project_id: uuid.UUID, name_query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        needle = name_query.casefold()
        matches = [r for r in self._rows if needle in r["feature_name"].casefold()]
        return sorted(
            matches, key=lambda r: (len(r["feature_name"]), r["feature_name"])
        )

    async def summarise_project(self, project_id: uuid.UUID) -> list[dict[str, Any]]:
        return self._summary


class FakeDatasetRepo:
    def __init__(self, datasets: list[Any] | None = None) -> None:
        self._datasets = DATASETS if datasets is None else datasets

    async def find_by_project(self, project_id: uuid.UUID) -> list[Any]:
        return self._datasets


class FakeUoW:
    """Stands in for UnitOfWork. Re-entrant, like the real sequential usage."""

    def __init__(
        self,
        rows: list[dict[str, Any]] | None = None,
        summary: list[dict[str, Any]] | None = None,
        datasets: list[Any] | None = None,
    ) -> None:
        self.dataset_features = FakeFeatureRepo(rows, summary)
        self.datasets = FakeDatasetRepo(datasets)
        self.enter_count = 0

    async def __aenter__(self) -> "FakeUoW":
        self.enter_count += 1
        return self

    async def __aexit__(self, *exc: Any) -> None:
        return None


class FakeInterpreter:
    """Returns a scripted intent and records what it was shown.

    Standing in for Claude here is the point: the pipeline is proven without a
    network call, an API key, or any nondeterminism.
    """

    def __init__(self, intent: SpatialIntent) -> None:
        self._intent = intent
        self.seen_catalogue: ProjectCatalogue | None = None
        self.seen_query: str | None = None

    async def interpret(self, query: str, catalogue: ProjectCatalogue) -> SpatialIntent:
        self.seen_query = query
        self.seen_catalogue = catalogue
        return self._intent


class RecordingDatasetService:
    """Captures which primitive was called with which arguments."""

    def __init__(self, features: list[dict[str, Any]] | None = None) -> None:
        self._features = features or []
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def query_nearby(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("nearby", kwargs))
        return {"type": "FeatureCollection", "features": self._features}

    async def query_contains(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("contains", kwargs))
        return {"type": "FeatureCollection", "features": self._features}

    async def query_intersects(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("intersects", kwargs))
        return {"type": "FeatureCollection", "features": self._features}
