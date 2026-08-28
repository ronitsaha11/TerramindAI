import pytest

from src.nlq.models import SpatialIntent
from src.nlq.resolver import ResolutionFailure, SpatialResolver
from tests.unit.nlq.fakes import BANGALORE_ID, PROJECT_ID, TEST_DATA_ID, FakeUoW


@pytest.fixture
def resolver():
    return SpatialResolver(FakeUoW())


async def test_catalogue_lists_datasets_and_categories(resolver):
    catalogue = await resolver.load_catalogue(PROJECT_ID)

    assert catalogue.dataset_names() == {"bangalore osm", "test data"}
    assert catalogue.category_values() == {"hospital", "park", "station"}


async def test_place_lookup_returns_every_match_shortest_first(resolver):
    """Resolution reports all matches; choosing between them is not its job."""
    places = await resolver.find_places(PROJECT_ID, "Lalbagh")

    assert [p.feature_name for p in places] == [
        "Lalbagh",
        "Lalbagh Nursing Home",
        "Lalbagh Botanical Gardens",
    ]


async def test_place_lookup_is_case_insensitive(resolver):
    assert await resolver.find_places(PROJECT_ID, "lalbagh")


async def test_unknown_place_returns_nothing(resolver):
    assert await resolver.find_places(PROJECT_ID, "Atlantis") == []


async def test_invented_category_is_refused(resolver):
    """A category the model made up cannot reach the engine."""
    catalogue = await resolver.load_catalogue(PROJECT_ID)
    place = (await resolver.find_places(PROJECT_ID, "Lalbagh Botanical"))[0]
    intent = SpatialIntent(
        operation="nearby",
        reference_place="Lalbagh Botanical Gardens",
        target_category="airport",
        distance_meters=2000,
    )

    with pytest.raises(ResolutionFailure, match="airport"):
        await resolver.resolve(PROJECT_ID, intent, catalogue, place)


async def test_invented_dataset_is_refused(resolver):
    catalogue = await resolver.load_catalogue(PROJECT_ID)
    place = (await resolver.find_places(PROJECT_ID, "Lalbagh Botanical"))[0]
    intent = SpatialIntent(
        operation="nearby",
        reference_place="Lalbagh Botanical Gardens",
        target_dataset="secret dataset",
        distance_meters=2000,
    )

    with pytest.raises(ResolutionFailure, match="secret dataset"):
        await resolver.resolve(PROJECT_ID, intent, catalogue, place)


async def test_nearby_defaults_to_the_dataset_holding_the_place(resolver):
    catalogue = await resolver.load_catalogue(PROJECT_ID)
    place = (await resolver.find_places(PROJECT_ID, "Lalbagh Botanical"))[0]
    intent = SpatialIntent(
        operation="nearby",
        reference_place="Lalbagh Botanical Gardens",
        target_category="hospital",
        distance_meters=2000,
    )

    resolved = await resolver.resolve(PROJECT_ID, intent, catalogue, place)

    assert resolved.dataset_id == BANGALORE_ID
    assert resolved.category == "hospital"
    assert resolved.radius_meters == 2000


async def test_category_matching_ignores_case(resolver):
    catalogue = await resolver.load_catalogue(PROJECT_ID)
    place = (await resolver.find_places(PROJECT_ID, "Lalbagh Botanical"))[0]
    intent = SpatialIntent(
        operation="nearby",
        reference_place="Lalbagh Botanical Gardens",
        target_category="HOSPITAL",
        distance_meters=2000,
    )

    resolved = await resolver.resolve(PROJECT_ID, intent, catalogue, place)

    assert resolved.category == "hospital"


async def test_intersects_resolves_the_named_target_dataset(resolver):
    catalogue = await resolver.load_catalogue(PROJECT_ID)
    place = (await resolver.find_places(PROJECT_ID, "Lalbagh Botanical"))[0]
    intent = SpatialIntent(
        operation="intersects",
        reference_place="Lalbagh Botanical Gardens",
        target_dataset="test data",
    )

    resolved = await resolver.resolve(PROJECT_ID, intent, catalogue, place)

    assert resolved.target_dataset_id == TEST_DATA_ID
    assert resolved.dataset_id == BANGALORE_ID
