import time
import uuid
from datetime import UTC, datetime
from typing import Any

from shapely.geometry import mapping

from src.geospatial.exceptions import GeoJSONExportError, GeoJSONValidationError
from src.geospatial.models import GeoJSONExportRequest, GeoJSONExportResult


class GeoJSONExporter:
    """Engine for serializing spatial analytics into RFC 7946 compliant GeoJSON."""

    def _validate_request(self, request: GeoJSONExportRequest) -> None:
        """Validate the incoming export request."""
        analytics_result = request.spatial_analytics_result
        if analytics_result is None:
            raise GeoJSONValidationError("Missing spatial analytics result.")

        if not hasattr(analytics_result, "analyzed_features"):
            raise GeoJSONValidationError("Malformed spatial analytics result.")

        # We do not strictly reject empty feature collections, but if it is None
        # we reject it. If it is an empty list, we return an empty FeatureCollection.

    def export(self, request: GeoJSONExportRequest) -> GeoJSONExportResult:
        """
        Serialize analytics results to a GeoJSON FeatureCollection.
        """
        try:
            self._validate_request(request)
        except GeoJSONValidationError:
            raise
        except Exception as e:
            raise GeoJSONExportError(f"Validation failed: {str(e)}") from e

        start_time = time.perf_counter()

        analytics_result = request.spatial_analytics_result
        features_list: list[dict[str, Any]] = []

        try:
            for analyzed_feature in analytics_result.analyzed_features:
                feature = analyzed_feature["feature"]
                stats = analyzed_feature["statistics"]

                # We map the Shapely geometry directly to GeoJSON
                geom_dict = mapping(feature.geometry)

                # Construct properties
                properties = {
                    "feature_id": str(uuid.uuid4()),
                    "class_value": feature.class_value,
                    "area_sqm": stats.area_sqm,
                    "perimeter_m": stats.perimeter_m,
                    "centroid": list(stats.centroid),
                    "bbox": list(stats.bbox),
                    "geometry_type": stats.geometry_type,
                }

                # Construct Feature
                geojson_feature = {
                    "type": "Feature",
                    "geometry": geom_dict,
                    "properties": properties,
                }
                features_list.append(geojson_feature)

            timestamp = datetime.now(UTC).isoformat()

            # Compile metadata
            export_metadata = {
                "feature_count": len(features_list),
                "export_timestamp": timestamp,
                "original_crs": analytics_result.crs,
                "analytics_metadata": analytics_result.metadata,
                "dataset_summary": analytics_result.dataset_summary,
            }

            # Assemble FeatureCollection
            feature_collection = {
                "type": "FeatureCollection",
                "features": features_list,
                "metadata": export_metadata,  # Extra member allowed by RFC 7946
            }

        except Exception as e:
            raise GeoJSONExportError(f"Failed to serialize GeoJSON: {str(e)}") from e

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000.0

        return GeoJSONExportResult(
            feature_collection=feature_collection,
            export_metadata=export_metadata,
            export_duration_ms=duration_ms,
        )
