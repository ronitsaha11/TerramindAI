import pytest
from pydantic import ValidationError

from src.schemas.region import RegionCreate
from src.utils.geometry import geojson_to_wkt


def test_polygon_input_is_normalized_to_multipolygon_wkt():
    geometry = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    }

    request = RegionCreate(name="Valid", geometry=geometry)

    assert geojson_to_wkt(request.geometry).startswith("MULTIPOLYGON")


@pytest.mark.parametrize(
    "geometry",
    [
        {"type": "Point", "coordinates": [0, 0]},
        {"type": "Polygon", "coordinates": []},
        {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]],
        },
    ],
)
def test_region_create_rejects_invalid_or_unsupported_geometry(geometry):
    with pytest.raises(ValidationError):
        RegionCreate(name="Invalid", geometry=geometry)
