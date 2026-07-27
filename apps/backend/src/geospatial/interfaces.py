from typing import Protocol

from src.geospatial.models import (
    GeoJSONExportRequest,
    GeoJSONExportResult,
    GeometryProcessingRequest,
    GeometryProcessingResult,
    PolygonizationRequest,
    PolygonizationResult,
    SpatialAnalyticsRequest,
    SpatialAnalyticsResult,
)


class PolygonizerProtocol(Protocol):
    """Protocol defining the polygonization behavior."""

    def polygonize(self, request: PolygonizationRequest) -> PolygonizationResult:
        """
        Convert a semantic raster mask into vector polygons.

        Args:
            request: The polygonization request.

        Returns:
            The polygonization result containing vector features.

        Raises:
            PolygonizationError: If polygonization fails.
            TransformValidationError: If the affine transform is invalid.
        """
        ...


class GeometryProcessorProtocol(Protocol):
    """Protocol defining the geometry processing behavior."""

    def process(self, request: GeometryProcessingRequest) -> GeometryProcessingResult:
        """
        Process and clean polygonized vector geometries.

        Args:
            request: The geometry processing request.

        Returns:
            The processed geometry result.

        Raises:
            GeometryProcessingError: If processing fails.
        """
        ...


class SpatialAnalyticsEngineProtocol(Protocol):
    """Protocol defining the spatial analytics behavior."""

    def analyze(self, request: SpatialAnalyticsRequest) -> SpatialAnalyticsResult:
        """
        Extract quantitative spatial intelligence from geometries.

        Args:
            request: The spatial analytics request.

        Returns:
            The spatial analytics result containing features and statistics.

        Raises:
            SpatialAnalyticsError: If analytics processing fails.
        """
        ...


class GeoJSONExporterProtocol(Protocol):
    """Protocol defining the GeoJSON export behavior."""

    def export(self, request: GeoJSONExportRequest) -> GeoJSONExportResult:
        """
        Serialize analytics results to a GeoJSON FeatureCollection.

        Args:
            request: The export request containing spatial analytics results.

        Returns:
            The GeoJSON export result containing the FeatureCollection dictionary.

        Raises:
            GeoJSONExportError: If export serialization fails.
        """
        ...
