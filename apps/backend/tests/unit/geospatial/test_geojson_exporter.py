import json

import pytest
from shapely.geometry import MultiPolygon, Polygon

from src.geospatial.exceptions import GeoJSONExportError
from src.geospatial.geojson_exporter import GeoJSONExporter
from src.geospatial.models import (
    GeoJSONExportRequest,
    PolygonFeature,
    SpatialAnalyticsResult,
    SpatialStatistics,
)


@pytest.fixture
def exporter() -> GeoJSONExporter:
    return GeoJSONExporter()


@pytest.fixture
def sample_analytics_result() -> SpatialAnalyticsResult:
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
    feature = PolygonFeature(class_value=1, geometry=poly)
    stats = SpatialStatistics(
        geometry_type="Polygon",
        area_sqm=100.0,
        perimeter_m=40.0,
        centroid=(5.0, 5.0),
        bbox=(0.0, 0.0, 10.0, 10.0),
    )

    return SpatialAnalyticsResult(
        analyzed_features=[{"feature": feature, "statistics": stats}],
        dataset_summary={"feature_count": 1},
        crs="EPSG:4326",
        metadata={"original_id": "test_scene"},
        processing_duration_ms=5.0,
    )


def test_feature_and_collection_generation(
    exporter: GeoJSONExporter, sample_analytics_result: SpatialAnalyticsResult
) -> None:
    req = GeoJSONExportRequest(spatial_analytics_result=sample_analytics_result)
    result = exporter.export(req)

    fc = result.feature_collection
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 1

    feature = fc["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Polygon"

    # Assert JSON serializability
    json_str = json.dumps(fc)
    assert isinstance(json_str, str)


def test_polygon_and_multipolygon_export(
    exporter: GeoJSONExporter, sample_analytics_result: SpatialAnalyticsResult
) -> None:
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
    multi = MultiPolygon(
        [poly, Polygon([(20, 20), (30, 20), (30, 30), (20, 30), (20, 20)])]
    )

    feature2 = PolygonFeature(class_value=2, geometry=multi)
    stats2 = SpatialStatistics(
        geometry_type="MultiPolygon",
        area_sqm=200.0,
        perimeter_m=80.0,
        centroid=(15.0, 15.0),
        bbox=(0.0, 0.0, 30.0, 30.0),
    )

    # Append to existing
    sample_analytics_result.analyzed_features.append(
        {"feature": feature2, "statistics": stats2}
    )

    req = GeoJSONExportRequest(spatial_analytics_result=sample_analytics_result)
    result = exporter.export(req)

    fc = result.feature_collection
    assert len(fc["features"]) == 2
    assert fc["features"][0]["geometry"]["type"] == "Polygon"
    assert fc["features"][1]["geometry"]["type"] == "MultiPolygon"


def test_analytics_property_preservation(
    exporter: GeoJSONExporter, sample_analytics_result: SpatialAnalyticsResult
) -> None:
    req = GeoJSONExportRequest(spatial_analytics_result=sample_analytics_result)
    result = exporter.export(req)

    props = result.feature_collection["features"][0]["properties"]

    assert "feature_id" in props
    assert props["class_value"] == 1
    assert props["area_sqm"] == 100.0
    assert props["perimeter_m"] == 40.0
    assert props["centroid"] == [5.0, 5.0]
    assert props["bbox"] == [0.0, 0.0, 10.0, 10.0]
    assert props["geometry_type"] == "Polygon"


def test_rfc7946_compliance(
    exporter: GeoJSONExporter, sample_analytics_result: SpatialAnalyticsResult
) -> None:
    req = GeoJSONExportRequest(spatial_analytics_result=sample_analytics_result)
    result = exporter.export(req)

    fc = result.feature_collection
    # Must NOT have deprecated crs
    assert "crs" not in fc

    # Original CRS preserved in metadata
    assert fc["metadata"]["original_crs"] == "EPSG:4326"
    assert "export_timestamp" in fc["metadata"]


def test_empty_collection_handling(exporter: GeoJSONExporter) -> None:
    empty_result = SpatialAnalyticsResult(
        analyzed_features=[],
        dataset_summary={},
        crs="EPSG:4326",
        metadata={},
        processing_duration_ms=0.0,
    )
    req = GeoJSONExportRequest(spatial_analytics_result=empty_result)
    result = exporter.export(req)

    fc = result.feature_collection
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 0
    assert fc["metadata"]["feature_count"] == 0


def test_exception_wrapping(
    exporter: GeoJSONExporter,
    sample_analytics_result: SpatialAnalyticsResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mock_mapping(*args: any, **kwargs: any) -> any:
        raise ValueError("Mapping failed")

    import src.geospatial.geojson_exporter

    monkeypatch.setattr(src.geospatial.geojson_exporter, "mapping", mock_mapping)

    req = GeoJSONExportRequest(spatial_analytics_result=sample_analytics_result)

    with pytest.raises(
        GeoJSONExportError, match="Failed to serialize GeoJSON: Mapping failed"
    ):
        exporter.export(req)
