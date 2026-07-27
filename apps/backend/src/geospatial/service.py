from src.geospatial.exceptions import (
    GeospatialExecutionError,
    GeospatialProcessingError,
)
from src.geospatial.interfaces import (
    GeoJSONExporterProtocol,
    GeometryProcessorProtocol,
    PolygonizerProtocol,
    SpatialAnalyticsEngineProtocol,
)
from src.geospatial.models import (
    GeoJSONExportRequest,
    GeoJSONExportResult,
    GeometryProcessingRequest,
    PolygonizationRequest,
    SpatialAnalyticsRequest,
)


class GeospatialService:
    """Application-layer orchestrator for the geospatial processing pipeline."""

    def __init__(
        self,
        polygonizer: PolygonizerProtocol,
        geometry_processor: GeometryProcessorProtocol,
        analytics_engine: SpatialAnalyticsEngineProtocol,
        geojson_exporter: GeoJSONExporterProtocol,
    ) -> None:
        """
        Initialize the GeospatialService with its dependencies.

        Args:
            polygonizer: Engine responsible for converting rasters to polygons.
            geometry_processor: Engine responsible for cleaning geometries.
            analytics_engine: Engine responsible for computing spatial metrics.
            geojson_exporter: Engine responsible for serializing to GeoJSON.
        """
        self._polygonizer = polygonizer
        self._geometry_processor = geometry_processor
        self._analytics_engine = analytics_engine
        self._geojson_exporter = geojson_exporter

    def process_mask(self, request: PolygonizationRequest) -> GeoJSONExportResult:
        """
        Execute the full geospatial pipeline from raster mask to GeoJSON.

        Args:
            request: The initial polygonization request containing the raster mask.

        Returns:
            The final GeoJSON export result.

        Raises:
            GeospatialExecutionError: If any stage in the pipeline fails.
        """
        try:
            # Step 1: Raster Polygonization
            polygonization_result = self._polygonizer.polygonize(request)

            # Step 2: Geometry Processing & Cleanup
            geom_request = GeometryProcessingRequest(
                polygonization_result=polygonization_result
            )
            geom_result = self._geometry_processor.process(geom_request)

            # Step 3: Spatial Analytics
            analytics_request = SpatialAnalyticsRequest(
                geometry_processing_result=geom_result
            )
            analytics_result = self._analytics_engine.analyze(analytics_request)

            # Step 4: GeoJSON Export
            export_request = GeoJSONExportRequest(
                spatial_analytics_result=analytics_result
            )
            export_result = self._geojson_exporter.export(export_request)

            return export_result

        except GeospatialProcessingError as e:
            # Wrap all underlying domain errors into a unified execution error.
            raise GeospatialExecutionError(
                f"Geospatial pipeline failed: {str(e)}"
            ) from e
        except Exception as e:
            # Catch unexpected errors to prevent implementation details from leaking.
            raise GeospatialExecutionError(
                f"Unexpected pipeline failure: {str(e)}"
            ) from e
