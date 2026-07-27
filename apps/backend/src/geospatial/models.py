from typing import Any

import numpy as np
from affine import Affine
from pydantic import BaseModel, ConfigDict, Field, field_validator
from shapely.geometry import MultiPolygon, Polygon


class PolygonizationRequest(BaseModel):
    """Request payload for polygonizing a semantic mask."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    mask: np.ndarray = Field(
        ..., description="2D semantic segmentation mask (NumPy array)"
    )
    transform: Affine = Field(
        ..., description="Affine transform mapping pixel space to geographic space"
    )
    crs: str = Field(..., description="Coordinate Reference System (e.g., EPSG:4326)")
    connectivity: int = Field(default=4, description="Pixel connectivity (4 or 8)")

    @field_validator("mask", mode="before")
    def parse_mask(cls, v: Any) -> np.ndarray:
        if isinstance(v, list):
            return np.array(v)
        return v

    @field_validator("transform", mode="before")
    def parse_transform(cls, v: Any) -> Affine:
        if isinstance(v, list) and len(v) == 6:
            return Affine(*v)
        elif isinstance(v, list) and len(v) == 9:
            return Affine(*v[:6])
        return v


class PolygonFeature(BaseModel):
    """A vectorized feature extracted from a raster mask."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    class_value: int = Field(..., description="The semantic class value from the mask")
    geometry: Polygon | MultiPolygon = Field(..., description="The vector geometry")


class PolygonizationResult(BaseModel):
    """Result of polygonizing a raster mask."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    features: list[PolygonFeature] = Field(
        ..., description="List of generated polygon features"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional processing metadata"
    )
    processing_duration_ms: float = Field(
        ..., description="Duration of the polygonization process in milliseconds"
    )


class GeometryProcessingRequest(BaseModel):
    """Request payload for processing and cleaning polygonized geometries."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    polygonization_result: PolygonizationResult = Field(
        ..., description="The result from the RasterPolygonizer to be processed"
    )
    simplify_tolerance: float | None = Field(
        default=None, description="Tolerance for geometry simplification, if any"
    )
    min_polygon_area: float | None = Field(
        default=None, description="Minimum area for a polygon to be retained"
    )
    preserve_topology: bool = Field(
        default=True, description="Whether to preserve topology during simplification"
    )


class GeometryProcessingResult(BaseModel):
    """Result of processing and cleaning geometries."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    features: list[PolygonFeature] = Field(
        ..., description="List of processed polygon features"
    )
    crs: str = Field(..., description="Coordinate Reference System (e.g., EPSG:4326)")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional processing metadata"
    )
    processing_duration_ms: float = Field(
        ..., description="Duration of the geometry processing in milliseconds"
    )


class SpatialAnalyticsRequest(BaseModel):
    """Request payload for executing spatial analytics on processed geometries."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    geometry_processing_result: GeometryProcessingResult = Field(
        ..., description="The processed geometries to analyze"
    )


class SpatialStatistics(BaseModel):
    """Metrics calculated for a single feature."""

    model_config = ConfigDict(frozen=True)

    geometry_type: str = Field(
        ..., description="The geometry type (e.g. Polygon, MultiPolygon)"
    )
    area_sqm: float = Field(..., description="Area of the geometry in square meters")
    perimeter_m: float = Field(
        ..., description="Perimeter/length of the geometry in meters"
    )
    centroid: tuple[float, float] = Field(
        ..., description="Centroid (longitude, latitude) of the geometry"
    )
    bbox: tuple[float, float, float, float] = Field(
        ..., description="Bounding box (minx, miny, maxx, maxy)"
    )


class SpatialAnalyticsResult(BaseModel):
    """Result containing analytics for the requested geometries."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    analyzed_features: list[dict[str, Any]] = Field(
        ...,
        description=(
            "List of dictionaries pairing features with their SpatialStatistics"
        ),
    )
    dataset_summary: dict[str, Any] = Field(
        ..., description="Aggregated statistics for the entire dataset"
    )
    crs: str = Field(..., description="Coordinate Reference System (e.g., EPSG:4326)")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional processing metadata"
    )
    processing_duration_ms: float = Field(
        ..., description="Duration of the analytics processing in milliseconds"
    )


class GeoJSONExportRequest(BaseModel):
    """Request payload for exporting analytics to GeoJSON."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    spatial_analytics_result: SpatialAnalyticsResult = Field(
        ..., description="The analytics result to export"
    )


class GeoJSONExportResult(BaseModel):
    """Result of the GeoJSON export containing the FeatureCollection."""

    model_config = ConfigDict(frozen=True)

    feature_collection: dict[str, Any] = Field(
        ..., description="The resulting GeoJSON FeatureCollection dictionary"
    )
    export_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata concerning the export process"
    )
    export_duration_ms: float = Field(
        ..., description="Duration of the export process in milliseconds"
    )
