from typing import Protocol

from src.geospatial.models import (
    GeometryProcessingRequest,
    GeometryProcessingResult,
    PolygonizationRequest,
    PolygonizationResult,
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
