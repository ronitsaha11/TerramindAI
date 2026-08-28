import pytest
from pydantic import ValidationError

from src.nlq.models import (
    MAX_DISTANCE_METERS,
    DatasetSummary,
    ProjectCatalogue,
    SpatialIntent,
)
from tests.unit.nlq.fakes import SUMMARY_ROWS


def test_valid_nearby_intent():
    intent = SpatialIntent(
        operation="nearby",
        reference_place="Lalbagh",
        target_category="hospital",
        distance_meters=2000,
    )

    assert intent.operation == "nearby"
    assert intent.distance_meters == 2000


def test_intent_is_frozen():
    intent = SpatialIntent(
        operation="nearby", reference_place="Lalbagh", distance_meters=2000
    )

    with pytest.raises(ValidationError):
        intent.operation = "contains"


def test_unknown_operation_is_rejected():
    """The operation set is closed - there is no path to anything else."""
    with pytest.raises(ValidationError):
        SpatialIntent(
            operation="drop_table", reference_place="Lalbagh", distance_meters=10
        )


def test_extra_fields_are_rejected():
    """An invented field is a hard failure, never silently carried through."""
    with pytest.raises(ValidationError):
        SpatialIntent(
            operation="nearby",
            reference_place="Lalbagh",
            distance_meters=2000,
            raw_sql="SELECT 1",
        )


@pytest.mark.parametrize("distance", [0, -1, MAX_DISTANCE_METERS + 1])
def test_distance_bounds_are_enforced(distance):
    with pytest.raises(ValidationError):
        SpatialIntent(
            operation="nearby", reference_place="Lalbagh", distance_meters=distance
        )


def test_nearby_requires_a_distance():
    with pytest.raises(ValidationError, match="distance_meters"):
        SpatialIntent(operation="nearby", reference_place="Lalbagh")


def test_every_operation_requires_a_reference_place():
    for operation in ("nearby", "contains", "intersects"):
        with pytest.raises(ValidationError, match="reference_place"):
            SpatialIntent(
                operation=operation,
                distance_meters=2000,
                target_dataset="bangalore osm",
            )


def test_intersects_requires_a_target_dataset():
    with pytest.raises(ValidationError, match="target_dataset"):
        SpatialIntent(operation="intersects", reference_place="Lalbagh")


def test_catalogue_exposes_vocabulary():
    catalogue = ProjectCatalogue(
        datasets=[
            DatasetSummary(
                name=row["dataset_name"],
                feature_count=row["feature_count"],
                categories=row["categories"],
            )
            for row in SUMMARY_ROWS
        ]
    )

    assert catalogue.dataset_names() == {"bangalore osm", "test data"}
    assert catalogue.category_values() == {"hospital", "park", "station"}
