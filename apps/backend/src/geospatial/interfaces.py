from typing import Protocol

from src.geospatial.models import PolygonizationRequest, PolygonizationResult


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
