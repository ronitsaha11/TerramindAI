from unittest.mock import MagicMock

import numpy as np
import pytest
from affine import Affine

from src.geospatial.exceptions import (
    GeoJSONExportError,
    GeospatialExecutionError,
)
from src.geospatial.interfaces import (
    GeoJSONExporterProtocol,
    GeometryProcessorProtocol,
    PolygonizerProtocol,
    SpatialAnalyticsEngineProtocol,
)
from src.geospatial.models import (
    GeoJSONExportResult,
    GeometryProcessingResult,
    PolygonizationRequest,
    PolygonizationResult,
    SpatialAnalyticsResult,
)
from src.geospatial.service import GeospatialService


@pytest.fixture
def mock_polygonizer() -> MagicMock:
    return MagicMock(spec=PolygonizerProtocol)


@pytest.fixture
def mock_geometry_processor() -> MagicMock:
    return MagicMock(spec=GeometryProcessorProtocol)


@pytest.fixture
def mock_analytics_engine() -> MagicMock:
    return MagicMock(spec=SpatialAnalyticsEngineProtocol)


@pytest.fixture
def mock_geojson_exporter() -> MagicMock:
    return MagicMock(spec=GeoJSONExporterProtocol)


@pytest.fixture
def service(
    mock_polygonizer: MagicMock,
    mock_geometry_processor: MagicMock,
    mock_analytics_engine: MagicMock,
    mock_geojson_exporter: MagicMock,
) -> GeospatialService:
    return GeospatialService(
        polygonizer=mock_polygonizer,
        geometry_processor=mock_geometry_processor,
        analytics_engine=mock_analytics_engine,
        geojson_exporter=mock_geojson_exporter,
    )


def test_process_mask_success(
    service: GeospatialService,
    mock_polygonizer: MagicMock,
    mock_geometry_processor: MagicMock,
    mock_analytics_engine: MagicMock,
    mock_geojson_exporter: MagicMock,
) -> None:
    # Setup mock returns
    mock_poly_res = PolygonizationResult(
        features=[], metadata={}, processing_duration_ms=1.0
    )
    mock_polygonizer.polygonize.return_value = mock_poly_res

    mock_geom_res = GeometryProcessingResult(
        features=[], crs="EPSG:4326", metadata={}, processing_duration_ms=1.0
    )
    mock_geometry_processor.process.return_value = mock_geom_res

    mock_analytics_res = SpatialAnalyticsResult(
        analyzed_features=[],
        dataset_summary={},
        crs="EPSG:4326",
        metadata={},
        processing_duration_ms=1.0,
    )
    mock_analytics_engine.analyze.return_value = mock_analytics_res

    mock_export_res = GeoJSONExportResult(
        feature_collection={"type": "FeatureCollection", "features": []},
        export_metadata={},
        export_duration_ms=1.0,
    )
    mock_geojson_exporter.export.return_value = mock_export_res

    # Create dummy request
    mask = np.zeros((10, 10), dtype=np.uint8)
    transform = Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0)
    request = PolygonizationRequest(mask=mask, transform=transform, crs="EPSG:4326")

    # Execute
    result = service.process_mask(request)

    # Assertions
    assert result == mock_export_res

    # Verify execution order and injection
    mock_polygonizer.polygonize.assert_called_once_with(request)

    geom_call_args = mock_geometry_processor.process.call_args[0][0]
    assert geom_call_args.polygonization_result == mock_poly_res

    analytics_call_args = mock_analytics_engine.analyze.call_args[0][0]
    assert analytics_call_args.geometry_processing_result == mock_geom_res

    export_call_args = mock_geojson_exporter.export.call_args[0][0]
    assert export_call_args.spatial_analytics_result == mock_analytics_res


def test_process_mask_exception_wrapping(
    service: GeospatialService,
    mock_polygonizer: MagicMock,
    mock_geometry_processor: MagicMock,
    mock_analytics_engine: MagicMock,
    mock_geojson_exporter: MagicMock,
) -> None:
    # Setup mock to fail at the last step
    mock_poly_res = PolygonizationResult(
        features=[], metadata={}, processing_duration_ms=1.0
    )
    mock_polygonizer.polygonize.return_value = mock_poly_res

    mock_geom_res = GeometryProcessingResult(
        features=[], crs="EPSG:4326", metadata={}, processing_duration_ms=1.0
    )
    mock_geometry_processor.process.return_value = mock_geom_res

    mock_analytics_res = SpatialAnalyticsResult(
        analyzed_features=[],
        dataset_summary={},
        crs="EPSG:4326",
        metadata={},
        processing_duration_ms=1.0,
    )
    mock_analytics_engine.analyze.return_value = mock_analytics_res

    # Exporter raises an error
    mock_geojson_exporter.export.side_effect = GeoJSONExportError("Test export failure")

    request = PolygonizationRequest(
        mask=np.zeros((10, 10), dtype=np.uint8),
        transform=Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0),
        crs="EPSG:4326",
    )

    with pytest.raises(
        GeospatialExecutionError,
        match="Geospatial pipeline failed: Test export failure",
    ):
        service.process_mask(request)


def test_unexpected_exception_wrapping(
    service: GeospatialService,
    mock_polygonizer: MagicMock,
) -> None:
    # Simulate an unexpected ValueError during polygonization
    mock_polygonizer.polygonize.side_effect = ValueError("Unexpected system failure")

    request = PolygonizationRequest(
        mask=np.zeros((10, 10), dtype=np.uint8),
        transform=Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0),
        crs="EPSG:4326",
    )

    with pytest.raises(
        GeospatialExecutionError,
        match="Unexpected pipeline failure: Unexpected system failure",
    ):
        service.process_mask(request)


def test_stateless_behavior(
    service: GeospatialService,
    mock_polygonizer: MagicMock,
    mock_geometry_processor: MagicMock,
    mock_analytics_engine: MagicMock,
    mock_geojson_exporter: MagicMock,
) -> None:
    # Setup mock returns
    mock_polygonizer.polygonize.return_value = PolygonizationResult(
        features=[], metadata={}, processing_duration_ms=1.0
    )
    mock_geometry_processor.process.return_value = GeometryProcessingResult(
        features=[], crs="EPSG:4326", metadata={}, processing_duration_ms=1.0
    )
    mock_analytics_engine.analyze.return_value = SpatialAnalyticsResult(
        analyzed_features=[],
        dataset_summary={},
        crs="EPSG:4326",
        metadata={},
        processing_duration_ms=1.0,
    )
    mock_geojson_exporter.export.return_value = GeoJSONExportResult(
        feature_collection={"type": "FeatureCollection", "features": []},
        export_metadata={},
        export_duration_ms=1.0,
    )

    request = PolygonizationRequest(
        mask=np.zeros((10, 10), dtype=np.uint8),
        transform=Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0),
        crs="EPSG:4326",
    )

    # Call twice
    res1 = service.process_mask(request)
    res2 = service.process_mask(request)

    assert res1 == res2
    assert mock_polygonizer.polygonize.call_count == 2
    assert mock_geometry_processor.process.call_count == 2
    assert mock_analytics_engine.analyze.call_count == 2
    assert mock_geojson_exporter.export.call_count == 2
