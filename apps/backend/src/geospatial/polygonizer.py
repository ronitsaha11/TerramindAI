import time

import numpy as np
import rasterio.features
from affine import Affine
from shapely.geometry import MultiPolygon, Polygon, shape

from src.geospatial.exceptions import PolygonizationError, TransformValidationError
from src.geospatial.models import (
    PolygonFeature,
    PolygonizationRequest,
    PolygonizationResult,
)


class RasterPolygonizer:
    """Engine for converting raster masks into vector polygons."""

    def _validate_request(self, request: PolygonizationRequest) -> None:
        """Validate the inputs before processing."""
        if not isinstance(request.mask, np.ndarray):
            raise PolygonizationError("Mask must be a NumPy array.")

        if request.mask.ndim != 2:
            raise PolygonizationError("Mask must be a 2D array.")

        if request.mask.size == 0:
            raise PolygonizationError("Mask cannot be empty.")

        # Ensure the mask is integer type (required for shapes)
        if not np.issubdtype(request.mask.dtype, np.integer):
            raise PolygonizationError("Mask must have an integer data type.")

        if not isinstance(request.transform, Affine):
            raise TransformValidationError(
                "Transform must be an instance of affine.Affine."
            )

        # Ensure the affine transform is invertible
        if request.transform.determinant == 0:
            raise TransformValidationError(
                "Affine transform is not invertible (determinant is 0)."
            )

    def polygonize(self, request: PolygonizationRequest) -> PolygonizationResult:
        """
        Convert a semantic raster mask into vector polygons.

        Args:
            request: The polygonization request.

        Returns:
            The polygonization result containing vector features.
        """
        self._validate_request(request)

        start_time = time.perf_counter()

        features: list[PolygonFeature] = []

        try:
            # Generate shapes. The mask argument is used to ignore background (value 0).
            # We treat any non-zero value as valid for shape extraction.
            valid_mask = request.mask != 0

            shapes = rasterio.features.shapes(
                source=request.mask,
                mask=valid_mask,
                transform=request.transform,
                connectivity=request.connectivity,
            )

            for geom_dict, value in shapes:
                class_value = int(value)

                # Convert to shapely geometry
                geom = shape(geom_dict)

                # We only support Polygon and MultiPolygon, but shape() usually
                # returns Polygon. However, it's good practice to ensure it's
                # valid type as per model.
                if not isinstance(geom, (Polygon, MultiPolygon)):
                    # Depending on rasterio output, this shouldn't happen for
                    # valid shapes, but if it's a GeometryCollection or
                    # something else, we ignore or log.

                    # Typically shapes() returns Polygons.
                    continue

                features.append(
                    PolygonFeature(
                        class_value=class_value,
                        geometry=geom,
                    )
                )

        except Exception as e:
            raise PolygonizationError(f"Failed to polygonize mask: {str(e)}") from e

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000.0

        return PolygonizationResult(
            features=features,
            metadata={"crs": request.crs, "connectivity": request.connectivity},
            processing_duration_ms=duration_ms,
        )
