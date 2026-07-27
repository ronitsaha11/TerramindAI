import pytest
from shapely.geometry import MultiPolygon, Polygon

from src.geospatial.analytics import SpatialAnalyticsEngine
from src.geospatial.exceptions import AnalyticsValidationError, ProjectionError
from src.geospatial.models import (
    GeometryProcessingResult,
    PolygonFeature,
    SpatialAnalyticsRequest,
)


@pytest.fixture
def engine() -> SpatialAnalyticsEngine:
    return SpatialAnalyticsEngine()


def test_projected_crs_calculations(engine: SpatialAnalyticsEngine) -> None:
    # A 10x10 square in a projected CRS (meters)
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
    result = GeometryProcessingResult(
        features=[PolygonFeature(class_value=1, geometry=poly)],
        crs="EPSG:3857",  # Projected
        metadata={},
        processing_duration_ms=1.0,
    )
    req = SpatialAnalyticsRequest(geometry_processing_result=result)

    analytics = engine.analyze(req)

    assert len(analytics.analyzed_features) == 1
    stats = analytics.analyzed_features[0]["statistics"]

    assert stats.area_sqm == 100.0
    assert stats.perimeter_m == 40.0
    assert stats.geometry_type == "Polygon"
    assert stats.centroid == (5.0, 5.0)
    assert stats.bbox == (0.0, 0.0, 10.0, 10.0)


def test_epsg4326_reprojection(engine: SpatialAnalyticsEngine) -> None:
    # A polygon roughly 1 degree x 1 degree near the equator
    # 1 degree is roughly 111km, so area should be around 12,321,000,000 sqm
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    result = GeometryProcessingResult(
        features=[PolygonFeature(class_value=1, geometry=poly)],
        crs="EPSG:4326",  # Geographic
        metadata={},
        processing_duration_ms=1.0,
    )
    req = SpatialAnalyticsRequest(geometry_processing_result=result)

    analytics = engine.analyze(req)

    stats = analytics.analyzed_features[0]["statistics"]

    # Assert area is large and non-trivial (i.e. not 1.0 which would
    # happen without reprojection)
    assert stats.area_sqm > 1e10
    assert stats.perimeter_m > 400_000
    assert stats.centroid == (0.5, 0.5)


def test_polygon_and_multipolygon_support(engine: SpatialAnalyticsEngine) -> None:
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
    multi = MultiPolygon(
        [poly, Polygon([(20, 20), (30, 20), (30, 30), (20, 30), (20, 20)])]
    )

    result = GeometryProcessingResult(
        features=[
            PolygonFeature(class_value=1, geometry=poly),
            PolygonFeature(class_value=2, geometry=multi),
        ],
        crs="EPSG:3857",
        metadata={},
        processing_duration_ms=1.0,
    )
    req = SpatialAnalyticsRequest(geometry_processing_result=result)

    analytics = engine.analyze(req)

    assert len(analytics.analyzed_features) == 2
    assert analytics.analyzed_features[0]["statistics"].geometry_type == "Polygon"
    assert analytics.analyzed_features[1]["statistics"].geometry_type == "MultiPolygon"
    assert analytics.analyzed_features[1]["statistics"].area_sqm == 200.0


def test_dataset_summary_and_class_aggregation(engine: SpatialAnalyticsEngine) -> None:
    poly1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])  # Area 100
    poly2 = Polygon([(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)])  # Area 25
    poly3 = Polygon([(0, 0), (20, 0), (20, 20), (0, 20), (0, 0)])  # Area 400

    result = GeometryProcessingResult(
        features=[
            PolygonFeature(class_value=1, geometry=poly1),
            PolygonFeature(class_value=1, geometry=poly2),
            PolygonFeature(class_value=2, geometry=poly3),
        ],
        crs="EPSG:3857",
        metadata={"key": "value"},
        processing_duration_ms=1.0,
    )
    req = SpatialAnalyticsRequest(geometry_processing_result=result)

    analytics = engine.analyze(req)
    summary = analytics.dataset_summary

    assert summary["feature_count"] == 3
    assert summary["total_area"] == 525.0
    assert summary["average_area"] == 175.0
    assert summary["min_area"] == 25.0
    assert summary["max_area"] == 400.0

    assert 1 in summary["class_wise"]
    assert summary["class_wise"][1]["count"] == 2
    assert summary["class_wise"][1]["total_area"] == 125.0
    assert summary["class_wise"][1]["average_area"] == 62.5

    assert 2 in summary["class_wise"]
    assert summary["class_wise"][2]["count"] == 1
    assert summary["class_wise"][2]["total_area"] == 400.0
    assert summary["class_wise"][2]["average_area"] == 400.0

    assert analytics.metadata["key"] == "value"
    assert analytics.crs == "EPSG:3857"


def test_invalid_crs_rejection(engine: SpatialAnalyticsEngine) -> None:
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
    result = GeometryProcessingResult(
        features=[PolygonFeature(class_value=1, geometry=poly)],
        crs="INVALID_CRS",
        metadata={},
        processing_duration_ms=1.0,
    )
    req = SpatialAnalyticsRequest(geometry_processing_result=result)

    with pytest.raises(AnalyticsValidationError, match="Invalid CRS provided"):
        engine.analyze(req)


def test_empty_feature_rejection(engine: SpatialAnalyticsEngine) -> None:
    result = GeometryProcessingResult(
        features=[],
        crs="EPSG:4326",
        metadata={},
        processing_duration_ms=1.0,
    )
    req = SpatialAnalyticsRequest(geometry_processing_result=result)

    with pytest.raises(AnalyticsValidationError, match="Empty feature collection"):
        engine.analyze(req)


def test_exception_wrapping(
    engine: SpatialAnalyticsEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    def mock_transform(*args: any, **kwargs: any) -> any:
        from pyproj.exceptions import ProjError

        raise ProjError("Mocked ProjError")

    import src.geospatial.analytics

    monkeypatch.setattr(src.geospatial.analytics, "transform", mock_transform)

    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    result = GeometryProcessingResult(
        features=[PolygonFeature(class_value=1, geometry=poly)],
        crs="EPSG:4326",
        metadata={},
        processing_duration_ms=1.0,
    )
    req = SpatialAnalyticsRequest(geometry_processing_result=result)

    with pytest.raises(
        ProjectionError, match="Failed to project geometry: Mocked ProjError"
    ):
        engine.analyze(req)
