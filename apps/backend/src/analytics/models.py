from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.analytics.enums import AnalysisType, ProcessingStatus
from src.analytics.statistics.schemas import StatisticsSummary
from src.analytics.types import (
    BandIdentifier,
    BoundingBox,
    CoordinateReferenceSystem,
    GeoTransform,
    RasterResolution,
)


class BandInfo(BaseModel):
    """Metadata describing a single band within a raster."""

    identifier: BandIdentifier
    name: str | None = None
    common_name: str | None = None
    description: str | None = None
    nodata_value: float | None = None
    dtype: str | None = None


class RasterMetadata(BaseModel):
    """Core geospatial metadata extracted from a raster source."""

    crs: CoordinateReferenceSystem
    bounds: BoundingBox
    resolution: RasterResolution
    transform: GeoTransform
    bands: list[BandInfo]
    width: int
    height: int
    driver: str | None = None
    compression: str | None = None


class OutputOptions(BaseModel):
    """Configuration for how analysis results should be stored/delivered."""

    persist_raster: bool = True
    generate_thumbnail: bool = True
    export_format: str = Field(default="COG", description="Format like COG, GeoTIFF")
    # Additional options can be added here


class AnalysisRequest(BaseModel):
    """Domain model representing a request to run an analytics job."""

    project_id: UUID
    region_id: UUID
    scene_id: str
    area_of_interest: BoundingBox | None = None
    requested_analysis: AnalysisType
    selected_bands: list[BandIdentifier] | None = None
    output_options: OutputOptions = Field(default_factory=OutputOptions)

    model_config = ConfigDict(from_attributes=True)


class AnalysisResult(BaseModel):
    """Domain model representing the outcome of an analytics job."""

    analysis_id: UUID
    request: AnalysisRequest
    processing_status: ProcessingStatus
    created_at: datetime
    completed_at: datetime | None = None
    raster_metadata: RasterMetadata | None = None
    statistics: StatisticsSummary | None = None
    output_uri: str | None = None
    thumbnail_uri: str | None = None
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)
