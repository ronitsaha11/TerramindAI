"""
Earth Intelligence Engine - Analytics Module

This module provides the foundation for geospatial processing, raster manipulation,
and AI inference. It defines core abstractions and domain models without tying
them to any specific implementation or framework.
"""

from src.analytics.engine import AnalyticsEngine
from src.analytics.enums import AnalysisType, ProcessingStatus
from src.analytics.exceptions import (
    AnalysisValidationError,
    AnalyticsError,
    InvalidBandError,
    ProviderError,
    RasterMetadataError,
    RasterOpenError,
    RasterReadError,
    StatisticsError,
    UnsupportedRasterError,
)
from src.analytics.models import (
    AnalysisRequest,
    AnalysisResult,
    BandInfo,
    OutputOptions,
    RasterMetadata,
)
from src.analytics.providers.base import (
    MetadataExtractor,
    RasterProvider,
    StatisticsProvider,
)
from src.analytics.types import (
    AnalysisIdentifier,
    BandIdentifier,
    BoundingBox,
    CoordinateReferenceSystem,
    GeoTransform,
    PixelWindow,
    RasterResolution,
    SceneIdentifier,
)

__all__ = [
    "AnalyticsEngine",
    "AnalysisType",
    "ProcessingStatus",
    "AnalyticsError",
    "RasterOpenError",
    "RasterReadError",
    "RasterMetadataError",
    "UnsupportedRasterError",
    "InvalidBandError",
    "AnalysisValidationError",
    "StatisticsError",
    "ProviderError",
    "AnalysisRequest",
    "AnalysisResult",
    "BandInfo",
    "OutputOptions",
    "RasterMetadata",
    "MetadataExtractor",
    "RasterProvider",
    "StatisticsProvider",
    "AnalysisIdentifier",
    "BandIdentifier",
    "BoundingBox",
    "CoordinateReferenceSystem",
    "GeoTransform",
    "PixelWindow",
    "RasterResolution",
    "SceneIdentifier",
]
