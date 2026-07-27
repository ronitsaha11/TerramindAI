from typing import Any

import numpy as np
from affine import Affine
from pydantic import BaseModel, ConfigDict, Field
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
