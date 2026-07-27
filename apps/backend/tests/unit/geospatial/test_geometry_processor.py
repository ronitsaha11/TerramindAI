import pytest
from shapely.geometry import MultiPolygon, Polygon

from src.geospatial.exceptions import GeometryProcessingError, GeometryValidationError
from src.geospatial.geometry_processor import GeometryProcessor
from src.geospatial.models import (
    GeometryProcessingRequest,
    PolygonFeature,
    PolygonizationResult,
)


@pytest.fixture
def processor() -> GeometryProcessor:
    return GeometryProcessor()


@pytest.fixture
def valid_polygonization_result() -> PolygonizationResult:
    return PolygonizationResult(
        features=[
            PolygonFeature(
                class_value=1,
                geometry=Polygon([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]),
            )
        ],
        metadata={"crs": "EPSG:4326"},
        processing_duration_ms=10.0,
    )


def test_invalid_geometry_repair(processor: GeometryProcessor) -> None:
    # A bowtie polygon (self-intersecting) is invalid
    bowtie = Polygon([(0, 0), (0, 2), (2, 0), (2, 2), (0, 0)])
    assert not bowtie.is_valid

    result = PolygonizationResult(
        features=[PolygonFeature(class_value=1, geometry=bowtie)],
        metadata={"crs": "EPSG:4326"},
        processing_duration_ms=1.0,
    )

    req = GeometryProcessingRequest(polygonization_result=result)
    processed = processor.process(req)

    assert len(processed.features) == 1
    repaired_geom = processed.features[0].geometry
    assert repaired_geom.is_valid
    assert isinstance(repaired_geom, (Polygon, MultiPolygon))
    assert processed.features[0].class_value == 1


def test_geometry_simplification(
    processor: GeometryProcessor, valid_polygonization_result: PolygonizationResult
) -> None:
    # A polygon with a tiny jutting point
    complex_poly = Polygon(
        [(0, 0), (1, 0), (1.01, 0.01), (1.02, 0), (2, 0), (2, 2), (0, 2), (0, 0)]
    )
    valid_polygonization_result.features[0] = PolygonFeature(
        class_value=2, geometry=complex_poly
    )

    req = GeometryProcessingRequest(
        polygonization_result=valid_polygonization_result,
        simplify_tolerance=0.1,
    )
    processed = processor.process(req)

    assert len(processed.features) == 1
    simplified = processed.features[0].geometry

    # Outer ring coordinates of simplified should be fewer than the complex polygon
    assert len(simplified.exterior.coords) < len(complex_poly.exterior.coords)


def test_multipolygon_processing(processor: GeometryProcessor) -> None:
    # MultiPolygon with one large component (4 area) and one tiny component (0.01 area)
    large_poly = Polygon([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)])
    tiny_poly = Polygon([(3, 3), (3.1, 3), (3.1, 3.1), (3, 3.1), (3, 3)])

    multi = MultiPolygon([large_poly, tiny_poly])

    result = PolygonizationResult(
        features=[PolygonFeature(class_value=3, geometry=multi)],
        metadata={"crs": "EPSG:4326"},
        processing_duration_ms=1.0,
    )

    # Use a min area filter that drops tiny_poly but keeps large_poly
    req = GeometryProcessingRequest(
        polygonization_result=result,
        min_polygon_area=1.0,
    )

    processed = processor.process(req)

    assert len(processed.features) == 1
    geom = processed.features[0].geometry
    # Should collapse into a single Polygon since only one valid component remains
    assert isinstance(geom, Polygon)
    # Area should be exactly the large polygon area (4.0)
    assert geom.area == 4.0


def test_tiny_polygon_removal(
    processor: GeometryProcessor, valid_polygonization_result: PolygonizationResult
) -> None:
    # The valid polygon has area 4.0
    # Set min_polygon_area to 5.0, it should be dropped completely
    req = GeometryProcessingRequest(
        polygonization_result=valid_polygonization_result,
        min_polygon_area=5.0,
    )

    processed = processor.process(req)
    assert len(processed.features) == 0


def test_crs_class_metadata_preservation(
    processor: GeometryProcessor, valid_polygonization_result: PolygonizationResult
) -> None:
    valid_polygonization_result.metadata["extra"] = "value"

    req = GeometryProcessingRequest(polygonization_result=valid_polygonization_result)

    processed = processor.process(req)

    assert processed.crs == "EPSG:4326"
    assert processed.metadata["extra"] == "value"
    assert processed.metadata["original_processing_duration_ms"] == 10.0
    assert processed.processing_duration_ms >= 0
    assert processed.features[0].class_value == 1


def test_malformed_request_rejection(processor: GeometryProcessor) -> None:
    # Missing CRS in metadata
    result = PolygonizationResult(
        features=[],
        metadata={},
        processing_duration_ms=0.0,
    )

    req = GeometryProcessingRequest(polygonization_result=result)

    with pytest.raises(GeometryValidationError, match="Missing CRS"):
        processor.process(req)


def test_exception_wrapping(
    processor: GeometryProcessor,
    valid_polygonization_result: PolygonizationResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mock_make_valid(*args: any, **kwargs: any) -> any:
        raise ValueError("Shapely failure")

    import src.geospatial.geometry_processor

    monkeypatch.setattr(
        src.geospatial.geometry_processor, "make_valid", mock_make_valid
    )

    # Create an invalid polygon to trigger make_valid
    bowtie = Polygon([(0, 0), (0, 2), (2, 0), (2, 2), (0, 0)])
    valid_polygonization_result.features[0] = PolygonFeature(
        class_value=1, geometry=bowtie
    )

    req = GeometryProcessingRequest(polygonization_result=valid_polygonization_result)

    with pytest.raises(
        GeometryProcessingError, match="Geometry processing failed: Shapely failure"
    ):
        processor.process(req)
