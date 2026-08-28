import json

import pytest

from src.nlq.models import SpatialIntent
from src.nlq.service import NaturalQueryService
from tests.unit.nlq.fakes import (
    BANGALORE_ID,
    GARDENS_ID,
    PROJECT_ID,
    TEST_DATA_ID,
    FakeInterpreter,
    FakeUoW,
    RecordingDatasetService,
    feature,
)

GARDENS = "Lalbagh Botanical Gardens"


def build(intent, features=None, uow=None):
    interpreter = FakeInterpreter(intent)
    engine = RecordingDatasetService(features or [])
    service = NaturalQueryService(uow or FakeUoW(), engine, interpreter)
    return service, engine, interpreter


async def test_ambiguous_place_asks_instead_of_guessing():
    """The central safety property: 'Lalbagh' matches three features.

    Picking the shortest match would silently measure from a bus station when
    the user meant the gardens - a confident answer to a question nobody asked.
    Nothing may reach the spatial engine in this case.
    """
    intent = SpatialIntent(
        operation="nearby",
        reference_place="Lalbagh",
        target_category="hospital",
        distance_meters=2000,
    )
    service, engine, _ = build(intent)

    result = await service.answer(PROJECT_ID, "hospitals within 2km of Lalbagh")

    assert result.status == "ambiguous"
    assert len(result.candidates) == 3
    assert {c.feature_name for c in result.candidates} == {
        "Lalbagh",
        "Lalbagh Nursing Home",
        GARDENS,
    }
    assert result.result is None
    assert engine.calls == [], "the engine must not run on an ambiguous place"


async def test_unambiguous_place_runs_nearby_with_resolved_coordinates():
    intent = SpatialIntent(
        operation="nearby",
        reference_place=GARDENS,
        target_category="hospital",
        distance_meters=2000,
    )
    features = [feature("St Martha's", "hospital"), feature("Glass House", "park")]
    service, engine, _ = build(intent, features)

    result = await service.answer(PROJECT_ID, f"hospitals within 2km of {GARDENS}")

    assert result.status == "ok"
    assert len(engine.calls) == 1
    operation, kwargs = engine.calls[0]
    assert operation == "nearby"
    assert kwargs["dataset_id"] == BANGALORE_ID
    assert kwargs["radius_meters"] == 2000
    # Coordinates come from the resolved feature, never from the model.
    assert kwargs["lon"] == pytest.approx(77.5856)
    assert kwargs["lat"] == pytest.approx(12.9486)


async def test_category_filter_narrows_geometric_results():
    """The primitives are purely geometric; 'hospitals' is an attribute filter."""
    intent = SpatialIntent(
        operation="nearby",
        reference_place=GARDENS,
        target_category="hospital",
        distance_meters=2000,
    )
    features = [
        feature("St Martha's", "hospital"),
        feature("Glass House", "park"),
        feature("Lalbagh Metro", "station"),
    ]
    service, _, _ = build(intent, features)

    result = await service.answer(PROJECT_ID, "hospitals near the gardens")

    assert result.status == "ok"
    assert [f["properties"]["category"] for f in result.result["features"]] == [
        "hospital"
    ]
    assert result.answer == "Found 1 hospital within 2 km of Lalbagh Botanical Gardens."


async def test_no_category_returns_everything_the_engine_found():
    intent = SpatialIntent(
        operation="nearby", reference_place=GARDENS, distance_meters=1000
    )
    features = [feature("a", "hospital"), feature("b", "park")]
    service, _, _ = build(intent, features)

    result = await service.answer(PROJECT_ID, "what is near the gardens")

    assert len(result.result["features"]) == 2
    assert "2 features" in result.answer


async def test_counts_come_from_the_engine_not_the_model():
    intent = SpatialIntent(
        operation="nearby",
        reference_place=GARDENS,
        target_category="park",
        distance_meters=2000,
    )
    features = [feature(f"park-{i}", "park") for i in range(7)]
    service, _, _ = build(intent, features)

    result = await service.answer(PROJECT_ID, "parks near the gardens")

    assert "7 parks" in result.answer


async def test_contains_dispatches_with_the_resolved_feature_id():
    intent = SpatialIntent(operation="contains", reference_place=GARDENS)
    service, engine, _ = build(intent, [feature("Fossilized Tree", "park")])

    result = await service.answer(PROJECT_ID, f"what is inside {GARDENS}")

    operation, kwargs = engine.calls[0]
    assert operation == "contains"
    assert kwargs["feature_id"] == GARDENS_ID
    assert result.answer.endswith(f"inside {GARDENS}.")


async def test_intersects_dispatches_with_both_datasets():
    intent = SpatialIntent(
        operation="intersects", reference_place=GARDENS, target_dataset="test data"
    )
    service, engine, _ = build(intent, [])

    await service.answer(PROJECT_ID, f"what overlaps {GARDENS}")

    operation, kwargs = engine.calls[0]
    assert operation == "intersects"
    assert kwargs["dataset_id"] == BANGALORE_ID
    assert kwargs["target_dataset_id"] == TEST_DATA_ID


async def test_unknown_place_is_unresolved_and_runs_nothing():
    intent = SpatialIntent(
        operation="nearby", reference_place="Atlantis", distance_meters=2000
    )
    service, engine, _ = build(intent)

    result = await service.answer(PROJECT_ID, "hospitals near Atlantis")

    assert result.status == "unresolved"
    assert "Atlantis" in result.answer
    assert engine.calls == []


async def test_invented_category_is_reported_not_executed():
    intent = SpatialIntent(
        operation="nearby",
        reference_place=GARDENS,
        target_category="airport",
        distance_meters=2000,
    )
    service, engine, _ = build(intent)

    result = await service.answer(PROJECT_ID, "airports near the gardens")

    assert result.status == "unresolved"
    assert "airport" in result.answer
    assert engine.calls == []


async def test_injection_in_a_place_name_is_treated_as_data():
    """A hostile place name resolves to nothing; it is never interpolated."""
    intent = SpatialIntent(
        operation="nearby",
        reference_place="'; DROP TABLE datasets; --",
        distance_meters=2000,
    )
    service, engine, _ = build(intent)

    result = await service.answer(PROJECT_ID, "malicious")

    assert result.status == "unresolved"
    assert engine.calls == []


async def test_empty_project_short_circuits_before_the_model_runs():
    uow = FakeUoW(rows=[], summary=[])
    intent = SpatialIntent(
        operation="nearby", reference_place=GARDENS, distance_meters=2000
    )
    service, engine, interpreter = build(intent, uow=uow)

    result = await service.answer(PROJECT_ID, "anything")

    assert result.status == "unresolved"
    assert interpreter.seen_query is None, "no reason to call Claude with no data"
    assert engine.calls == []


async def test_model_is_shown_names_only_never_data():
    """What Claude sees is the whole attack surface - assert it stays vocabulary."""
    intent = SpatialIntent(
        operation="nearby", reference_place=GARDENS, distance_meters=2000
    )
    service, _, interpreter = build(intent)

    await service.answer(PROJECT_ID, "hospitals near the gardens")

    payload = json.dumps(interpreter.seen_catalogue.model_dump())
    assert "bangalore osm" in payload and "hospital" in payload
    for leak in (str(BANGALORE_ID), str(GARDENS_ID), "77.5", "12.9", "geometry"):
        assert leak not in payload, f"catalogue leaked {leak!r} to the model"
