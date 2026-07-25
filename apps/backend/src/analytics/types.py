from typing import NewType

from pydantic import BaseModel, Field

# Strong typing for scalar identifiers
BandIdentifier = NewType("BandIdentifier", str)
SceneIdentifier = NewType("SceneIdentifier", str)
AnalysisIdentifier = NewType("AnalysisIdentifier", str)
CoordinateReferenceSystem = NewType("CoordinateReferenceSystem", str)


class BoundingBox(BaseModel):
    """Represents a geospatial bounding box."""

    west: float = Field(ge=-180, le=180)
    south: float = Field(ge=-90, le=90)
    east: float = Field(ge=-180, le=180)
    north: float = Field(ge=-90, le=90)


class RasterResolution(BaseModel):
    """Represents the spatial resolution of a raster in its native CRS."""

    x: float = Field(gt=0)
    y: float = Field(gt=0)


class PixelWindow(BaseModel):
    """Represents a window (crop) of pixels within a raster."""

    col_off: int = Field(ge=0)
    row_off: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class GeoTransform(BaseModel):
    """Affine transformation parameters for a raster."""

    a: float
    b: float
    c: float
    d: float
    e: float
    f: float
