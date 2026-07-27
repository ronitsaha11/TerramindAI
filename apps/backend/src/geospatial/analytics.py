import time
from typing import Any

import pyproj
from pyproj.exceptions import CRSError, ProjError
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

from src.geospatial.exceptions import (
    AnalyticsValidationError,
    ProjectionError,
    SpatialAnalyticsError,
)
from src.geospatial.models import (
    SpatialAnalyticsRequest,
    SpatialAnalyticsResult,
    SpatialStatistics,
)


class SpatialAnalyticsEngine:
    """Engine for extracting spatial intelligence from geometries."""

    def _validate_request(self, request: SpatialAnalyticsRequest) -> pyproj.CRS:
        """Validate the incoming analytics request and parse CRS."""
        result = request.geometry_processing_result
        if not result.features:
            raise AnalyticsValidationError("Empty feature collection provided.")
        if not result.crs:
            raise AnalyticsValidationError("Missing CRS in geometry result.")

        try:
            crs_obj = pyproj.CRS.from_string(result.crs)
            return crs_obj
        except CRSError as e:
            raise AnalyticsValidationError(f"Invalid CRS provided: {str(e)}") from e

    def _compute_metrics(
        self, geom: BaseGeometry, crs_obj: pyproj.CRS
    ) -> tuple[float, float, tuple[float, float], tuple[float, float, float, float]]:
        """
        Compute area, perimeter, centroid, and bounding box.
        Dynamically projects if the CRS is geographic.
        Returns: (area_sqm, perimeter_m, (lon, lat), (minx, miny, maxx, maxy))
        """
        centroid = (geom.centroid.x, geom.centroid.y)
        bounds = geom.bounds

        if crs_obj.is_projected:
            area = geom.area
            perimeter = geom.length
        else:
            try:
                # Dynamic LAEA projection centered on the geometry for accurate metrics
                proj_string = (
                    f"+proj=laea +lat_0={geom.centroid.y} +lon_0={geom.centroid.x} "
                    f"+datum=WGS84 +units=m"
                )
                local_crs = pyproj.CRS(proj_string)
                transformer = pyproj.Transformer.from_crs(
                    crs_obj, local_crs, always_xy=True
                )

                # Transform geometry
                geom_proj = transform(transformer.transform, geom)
                area = geom_proj.area
                perimeter = geom_proj.length
            except ProjError as e:
                raise ProjectionError(f"Failed to project geometry: {str(e)}") from e
            except Exception as e:
                raise ProjectionError(f"Unexpected projection error: {str(e)}") from e

        return area, perimeter, centroid, bounds

    def analyze(self, request: SpatialAnalyticsRequest) -> SpatialAnalyticsResult:
        """
        Extract quantitative spatial intelligence from geometries.
        """
        try:
            crs_obj = self._validate_request(request)
        except AnalyticsValidationError:
            raise
        except Exception as e:
            raise SpatialAnalyticsError(f"Failed to validate request: {str(e)}") from e

        start_time = time.perf_counter()

        analyzed_features: list[dict[str, Any]] = []

        # Track statistics for dataset summary
        total_area = 0.0
        min_area = float("inf")
        max_area = 0.0
        total_perimeter = 0.0
        class_stats: dict[int, dict[str, float]] = {}

        try:
            for feature in request.geometry_processing_result.features:
                geom = feature.geometry
                class_value = feature.class_value

                area, perimeter, centroid, bounds = self._compute_metrics(geom, crs_obj)

                stats = SpatialStatistics(
                    geometry_type=geom.geom_type,
                    area_sqm=area,
                    perimeter_m=perimeter,
                    centroid=centroid,
                    bbox=bounds,
                )

                analyzed_features.append({"feature": feature, "statistics": stats})

                # Accumulate dataset-level stats
                total_area += area
                total_perimeter += perimeter
                if area < min_area:
                    min_area = area
                if area > max_area:
                    max_area = area

                if class_value not in class_stats:
                    class_stats[class_value] = {"count": 0.0, "total_area": 0.0}
                class_stats[class_value]["count"] += 1
                class_stats[class_value]["total_area"] += area

        except SpatialAnalyticsError:
            raise
        except Exception as e:
            raise SpatialAnalyticsError(f"Analytics processing failed: {str(e)}") from e

        count = len(analyzed_features)

        # Calculate class-wise average area
        class_wise_summary = {}
        for cv, data in class_stats.items():
            class_wise_summary[cv] = {
                "count": int(data["count"]),
                "total_area": data["total_area"],
                "average_area": data["total_area"] / data["count"]
                if data["count"] > 0
                else 0.0,
            }

        dataset_summary = {
            "feature_count": count,
            "total_area": total_area,
            "average_area": total_area / count if count > 0 else 0.0,
            "min_area": min_area if count > 0 else 0.0,
            "max_area": max_area if count > 0 else 0.0,
            "total_perimeter": total_perimeter,
            "class_wise": class_wise_summary,
        }

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000.0

        metadata = dict(request.geometry_processing_result.metadata)

        return SpatialAnalyticsResult(
            analyzed_features=analyzed_features,
            dataset_summary=dataset_summary,
            crs=request.geometry_processing_result.crs,
            metadata=metadata,
            processing_duration_ms=duration_ms,
        )
