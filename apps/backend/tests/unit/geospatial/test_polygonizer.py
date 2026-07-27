import numpy as np
import pytest
from affine import Affine
from shapely.geometry import Polygon

from src.geospatial.exceptions import PolygonizationError, TransformValidationError
from src.geospatial.models import PolygonizationRequest
from src.geospatial.polygonizer import RasterPolygonizer


@pytest.fixture
def valid_transform() -> Affine:
    return Affine.translation(10.0, 20.0) * Affine.scale(2.0, -2.0)


@pytest.fixture
def polygonizer() -> RasterPolygonizer:
    return RasterPolygonizer()


def test_successful_polygonization(
    polygonizer: RasterPolygonizer, valid_transform: Affine
) -> None:
    # A simple mask with one polygon of class 1
    mask = np.array(
        [
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
        dtype=np.int32,
    )

    req = PolygonizationRequest(
        mask=mask,
        transform=valid_transform,
        crs="EPSG:4326",
    )

    result = polygonizer.polygonize(req)

    assert len(result.features) == 1
    assert result.features[0].class_value == 1
    assert isinstance(result.features[0].geometry, Polygon)
    assert result.processing_duration_ms > 0
    assert result.metadata["crs"] == "EPSG:4326"


def test_affine_transform_correctness(
    polygonizer: RasterPolygonizer, valid_transform: Affine
) -> None:
    # 1 pixel at top left
    mask = np.array([[1]], dtype=np.int32)
    req = PolygonizationRequest(mask=mask, transform=valid_transform, crs="EPSG:4326")

    result = polygonizer.polygonize(req)
    assert len(result.features) == 1
    poly = result.features[0].geometry

    # Expected bounds based on the valid_transform:
    # Top-left corner: (10.0, 20.0)
    # Width: 2.0, Height: -2.0
    # Expected bounds: minx=10.0, miny=18.0, maxx=12.0, maxy=20.0
    assert poly.bounds == (10.0, 18.0, 12.0, 20.0)


def test_polygon_generation(
    polygonizer: RasterPolygonizer, valid_transform: Affine
) -> None:
    mask = np.zeros((10, 10), dtype=np.int32)
    mask[2:5, 2:5] = 2  # A 3x3 square

    req = PolygonizationRequest(mask=mask, transform=valid_transform, crs="EPSG:4326")
    result = polygonizer.polygonize(req)

    assert len(result.features) == 1
    assert result.features[0].class_value == 2
    assert isinstance(result.features[0].geometry, Polygon)


def test_multipolygon_generation(
    polygonizer: RasterPolygonizer, valid_transform: Affine
) -> None:
    mask = np.zeros((10, 10), dtype=np.int32)
    # Blob 1
    mask[1:3, 1:3] = 3
    # Blob 2 (disjoint)
    mask[7:9, 7:9] = 3

    req = PolygonizationRequest(mask=mask, transform=valid_transform, crs="EPSG:4326")
    result = polygonizer.polygonize(req)

    # rasterio.features.shapes yields individual polygons for disjoint
    # regions of the same class
    assert len(result.features) == 2
    assert result.features[0].class_value == 3
    assert result.features[1].class_value == 3
    for feat in result.features:
        assert isinstance(feat.geometry, Polygon)


def test_deterministic_ordering(
    polygonizer: RasterPolygonizer, valid_transform: Affine
) -> None:
    mask = np.array([[1, 0, 2], [0, 0, 0], [3, 0, 4]], dtype=np.int32)

    req = PolygonizationRequest(mask=mask, transform=valid_transform, crs="EPSG:4326")

    # Run multiple times to ensure the same number of features and same classes
    result1 = polygonizer.polygonize(req)
    result2 = polygonizer.polygonize(req)

    classes1 = [f.class_value for f in result1.features]
    classes2 = [f.class_value for f in result2.features]

    assert classes1 == classes2
    assert len(classes1) == 4


def test_background_filtering(
    polygonizer: RasterPolygonizer, valid_transform: Affine
) -> None:
    # All zeros
    mask = np.zeros((10, 10), dtype=np.int32)
    req = PolygonizationRequest(mask=mask, transform=valid_transform, crs="EPSG:4326")

    result = polygonizer.polygonize(req)
    assert len(result.features) == 0


def test_invalid_mask_rejection(
    polygonizer: RasterPolygonizer, valid_transform: Affine
) -> None:
    # Not a numpy array
    with pytest.raises(PolygonizationError, match="must be a NumPy array"):
        req = PolygonizationRequest.model_construct(
            mask=[[1, 1], [1, 1]], transform=valid_transform, crs="EPSG:4326"
        )
        polygonizer.polygonize(req)

    # Empty array
    with pytest.raises(PolygonizationError, match="cannot be empty"):
        req = PolygonizationRequest(
            mask=np.array([[]], dtype=np.int32),
            transform=valid_transform,
            crs="EPSG:4326",
        )
        polygonizer.polygonize(req)

    # Not 2D
    with pytest.raises(PolygonizationError, match="must be a 2D array"):
        req = PolygonizationRequest(
            mask=np.zeros((2, 2, 2), dtype=np.int32),
            transform=valid_transform,
            crs="EPSG:4326",
        )
        polygonizer.polygonize(req)

    # Unsupported dtype (float)
    with pytest.raises(PolygonizationError, match="integer data type"):
        req = PolygonizationRequest(
            mask=np.zeros((2, 2), dtype=np.float32),
            transform=valid_transform,
            crs="EPSG:4326",
        )
        polygonizer.polygonize(req)


def test_invalid_transform_rejection(polygonizer: RasterPolygonizer) -> None:
    mask = np.array([[1]], dtype=np.int32)

    # Not an affine transform
    with pytest.raises(TransformValidationError, match="instance of affine.Affine"):
        req = PolygonizationRequest.model_construct(
            mask=mask, transform="not_a_transform", crs="EPSG:4326"
        )
        polygonizer.polygonize(req)

    # Non-invertible transform (determinant 0)
    with pytest.raises(TransformValidationError, match="not invertible"):
        bad_transform = Affine(0, 0, 0, 0, 0, 0)
        req = PolygonizationRequest(mask=mask, transform=bad_transform, crs="EPSG:4326")
        polygonizer.polygonize(req)


def test_exception_wrapping(
    polygonizer: RasterPolygonizer,
    valid_transform: Affine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mask = np.array([[1]], dtype=np.int32)
    req = PolygonizationRequest(mask=mask, transform=valid_transform, crs="EPSG:4326")

    # Mock rasterio.features.shapes to raise an exception
    def mock_shapes(*args: any, **kwargs: any) -> any:
        raise ValueError("rasterio failure")

    import rasterio.features

    monkeypatch.setattr(rasterio.features, "shapes", mock_shapes)

    with pytest.raises(
        PolygonizationError, match="Failed to polygonize mask: rasterio failure"
    ):
        polygonizer.polygonize(req)
