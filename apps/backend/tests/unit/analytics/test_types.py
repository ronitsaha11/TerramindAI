import pytest
from pydantic import ValidationError

from src.analytics.types import (
    BoundingBox,
    CoordinateReferenceSystem,
    GeoTransform,
    PixelWindow,
    RasterResolution,
)


def test_bounding_box_valid() -> None:
    bbox = BoundingBox(west=-120.0, south=30.0, east=-110.0, north=40.0)
    assert bbox.west == -120.0
    assert bbox.north == 40.0


def test_bounding_box_invalid_latitude() -> None:
    with pytest.raises(ValidationError):
        BoundingBox(west=-120.0, south=-100.0, east=-110.0, north=40.0)


def test_pixel_window_valid() -> None:
    window = PixelWindow(col_off=10, row_off=20, width=256, height=256)
    assert window.width == 256
    assert window.col_off == 10


def test_pixel_window_invalid_width() -> None:
    with pytest.raises(ValidationError):
        PixelWindow(col_off=10, row_off=20, width=0, height=256)


def test_raster_resolution() -> None:
    res = RasterResolution(x=10.0, y=10.0)
    assert res.x == 10.0

    with pytest.raises(ValidationError):
        RasterResolution(x=-1.0, y=10.0)


def test_geo_transform() -> None:
    transform = GeoTransform(a=10.0, b=0.0, c=100.0, d=0.0, e=-10.0, f=200.0)
    assert transform.a == 10.0
    assert transform.f == 200.0


def test_type_aliases() -> None:
    crs = CoordinateReferenceSystem("EPSG:4326")
    assert crs == "EPSG:4326"
