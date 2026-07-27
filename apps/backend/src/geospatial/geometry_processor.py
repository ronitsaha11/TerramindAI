import time
from typing import cast

from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid

from src.geospatial.exceptions import GeometryProcessingError, GeometryValidationError
from src.geospatial.models import (
    GeometryProcessingRequest,
    GeometryProcessingResult,
    PolygonFeature,
)


class GeometryProcessor:
    """Engine for processing and cleaning up vectorized geometries."""

    def _validate_request(self, request: GeometryProcessingRequest) -> None:
        """Validate the incoming processing request."""
        # A valid CRS must be present. Usually we'll expect it in PolygonizationResult
        # or we might expect it to be passed through metadata, but here it's part of
        # the feature set or we can extract it from metadata.
        # Wait, the prompt says "reject missing CRS".
        # Let's check the request.polygonization_result.metadata for "crs".
        crs = request.polygonization_result.metadata.get("crs")
        if not crs:
            raise GeometryValidationError(
                "Missing CRS in PolygonizationResult metadata."
            )

        if not request.polygonization_result.features:
            # We don't necessarily reject empty feature lists as malformed unless
            # required, but if it's explicitly malformed, we might. Let's just
            # process it (will return empty).
            pass

    def _process_geometry(
        self,
        geom: BaseGeometry,
        simplify_tolerance: float | None,
        min_polygon_area: float | None,
        preserve_topology: bool,
    ) -> Polygon | MultiPolygon | None:
        """
        Process a single geometry.

        Applies make_valid, simplification, and area filtering.
        """
        # Repair invalid geometries
        if not geom.is_valid:
            geom = make_valid(geom)

        # Simplify
        if simplify_tolerance is not None and simplify_tolerance > 0:
            geom = geom.simplify(
                tolerance=simplify_tolerance, preserve_topology=preserve_topology
            )

        # We only process Polygon and MultiPolygon, but make_valid could return
        # GeometryCollection or other types (e.g. LineString if collapsed).
        # Extract all Polygons from the geometry.
        polygons: list[Polygon] = []

        if isinstance(geom, Polygon):
            polygons.append(geom)
        elif isinstance(geom, MultiPolygon):
            polygons.extend(list(geom.geoms))
        elif isinstance(geom, GeometryCollection):
            # Extract polygons from collection
            for part in geom.geoms:
                if isinstance(part, Polygon):
                    polygons.append(part)
                elif isinstance(part, MultiPolygon):
                    polygons.extend(list(part.geoms))
        else:
            # Other geometry types (LineString, Point) generated during make_valid
            # are discarded because we only care about polygons.
            pass

        # Filter by area
        if min_polygon_area is not None and min_polygon_area > 0:
            valid_polygons = [p for p in polygons if p.area >= min_polygon_area]
        else:
            valid_polygons = polygons

        if not valid_polygons:
            return None

        if len(valid_polygons) == 1:
            return valid_polygons[0]
        else:
            return MultiPolygon(valid_polygons)

    def process(self, request: GeometryProcessingRequest) -> GeometryProcessingResult:
        """
        Process and clean polygonized vector geometries.

        Args:
            request: The geometry processing request.

        Returns:
            The processed geometry result.
        """
        try:
            self._validate_request(request)
        except GeometryValidationError:
            raise
        except Exception as e:
            raise GeometryProcessingError(
                f"Failed to validate request: {str(e)}"
            ) from e

        start_time = time.perf_counter()

        processed_features: list[PolygonFeature] = []

        try:
            for feature in request.polygonization_result.features:
                processed_geom = self._process_geometry(
                    geom=feature.geometry,
                    simplify_tolerance=request.simplify_tolerance,
                    min_polygon_area=request.min_polygon_area,
                    preserve_topology=request.preserve_topology,
                )

                if processed_geom is not None:
                    # We cast because _process_geometry guarantees Polygon or
                    # MultiPolygon.
                    processed_geom = cast(Polygon | MultiPolygon, processed_geom)
                    processed_features.append(
                        PolygonFeature(
                            class_value=feature.class_value,
                            geometry=processed_geom,
                        )
                    )

        except Exception as e:
            raise GeometryProcessingError(
                f"Geometry processing failed: {str(e)}"
            ) from e

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000.0

        # Original polygonization duration can be preserved in metadata
        metadata = dict(request.polygonization_result.metadata)
        metadata["original_processing_duration_ms"] = (
            request.polygonization_result.processing_duration_ms
        )

        return GeometryProcessingResult(
            features=processed_features,
            crs=metadata["crs"],
            metadata=metadata,
            processing_duration_ms=duration_ms,
        )
