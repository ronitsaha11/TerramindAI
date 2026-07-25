"""
Unit tests for the AnalysisService orchestration layer.
All raster I/O, spectral computation, and statistics are mocked.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import numpy as np
import pytest

from src.analytics.enums import AnalysisType, ProcessingStatus
from src.analytics.exceptions import (
    AnalysisValidationError,
    ProviderError,
    RasterOpenError,
    StatisticsError,
)
from src.analytics.indices.ndvi import NDVIIndex
from src.analytics.indices.registry import IndexRegistry
from src.analytics.models import (
    AnalysisRequest,
    BandInfo,
    OutputOptions,
    RasterMetadata,
)
from src.analytics.statistics.engine import StatisticsEngine
from src.analytics.statistics.schemas import PercentileResult, StatisticsSummary
from src.analytics.types import (
    BandIdentifier,
    BoundingBox,
    CoordinateReferenceSystem,
    GeoTransform,
    RasterResolution,
)
from src.services.analysis_service import AnalysisService

# -------------------------------------------------------------------
# Helpers / shared fixtures
# -------------------------------------------------------------------


def make_request(
    analysis_type: AnalysisType = AnalysisType.NDVI,
    scene_id: str = "s3://bucket/scene.tif",
) -> AnalysisRequest:
    return AnalysisRequest(
        project_id=uuid4(),
        region_id=uuid4(),
        scene_id=scene_id,
        requested_analysis=analysis_type,
        output_options=OutputOptions(),
    )


def make_raster_metadata(band_count: int = 2) -> RasterMetadata:
    bands = [
        BandInfo(identifier=BandIdentifier(str(i)), dtype="uint16")
        for i in range(1, band_count + 1)
    ]
    return RasterMetadata(
        crs=CoordinateReferenceSystem("EPSG:32610"),
        bounds=BoundingBox(west=-120.0, south=30.0, east=-119.0, north=31.0),
        resolution=RasterResolution(x=10.0, y=10.0),
        transform=GeoTransform(a=10.0, b=0.0, c=500000.0, d=0.0, e=-10.0, f=4000000.0),
        bands=bands,
        width=100,
        height=100,
        driver="GTiff",
    )


def make_statistics_summary() -> StatisticsSummary:
    return StatisticsSummary(
        min=-0.5,
        max=0.9,
        mean=0.4,
        median=0.45,
        variance=0.01,
        std_dev=0.1,
        valid_pixels=10000,
        nodata_pixels=0,
        nodata_percentage=0.0,
        finite_pixels=10000,
        percentiles=PercentileResult(p5=0.1, p25=0.3, p50=0.45, p75=0.6, p95=0.8),
    )


def make_mock_provider(metadata: RasterMetadata) -> AsyncMock:
    """
    Build a mock RasterProvider that behaves like an async context manager.
    read_band returns bytes that decode to a trivial float32 array.
    """
    band_data = np.ones(100 * 100, dtype=np.float32).tobytes()

    provider = AsyncMock()
    provider.__aenter__ = AsyncMock(return_value=provider)
    provider.__aexit__ = AsyncMock(return_value=None)
    provider.open = AsyncMock(return_value=None)
    provider.metadata = AsyncMock(return_value=metadata)
    provider.read_band = AsyncMock(return_value=band_data)
    return provider


def make_service(
    provider: AsyncMock,
    stats_summary: StatisticsSummary | None = None,
) -> AnalysisService:
    registry = IndexRegistry()
    registry.register(NDVIIndex())

    stats_engine = MagicMock(spec=StatisticsEngine)
    stats_engine.compute_statistics.return_value = (
        stats_summary if stats_summary is not None else make_statistics_summary()
    )

    return AnalysisService(
        raster_provider=provider,
        index_registry=registry,
        statistics_engine=stats_engine,
    )


# -------------------------------------------------------------------
# 1. Successful orchestration
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_success():
    metadata = make_raster_metadata(band_count=2)
    provider = make_mock_provider(metadata)
    service = make_service(provider)

    request = make_request(AnalysisType.NDVI)
    result = await service.analyze(request)

    assert result.processing_status == ProcessingStatus.COMPLETED
    assert result.analysis_id is not None
    assert result.raster_metadata is not None
    assert result.statistics is not None
    assert result.statistics.mean == 0.4
    assert result.error_message is None
    assert result.completed_at is not None

    provider.open.assert_awaited_once_with(request.scene_id)
    provider.metadata.assert_awaited_once()


# -------------------------------------------------------------------
# 2. Validation failure — empty scene_id
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_empty_scene_id():
    provider = make_mock_provider(make_raster_metadata())
    service = make_service(provider)
    request = make_request(scene_id="   ")

    with pytest.raises(AnalysisValidationError, match="scene_id must not be empty"):
        await service.analyze(request)

    provider.open.assert_not_awaited()


# -------------------------------------------------------------------
# 3. Validation failure — unsupported analysis type (not in registry)
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_unsupported_analysis_type():
    provider = make_mock_provider(make_raster_metadata())
    registry = IndexRegistry()  # empty — no NDWI registered
    stats_engine = MagicMock(spec=StatisticsEngine)
    service = AnalysisService(provider, registry, stats_engine)

    request = make_request(AnalysisType.NDWI)

    with pytest.raises(AnalysisValidationError, match="Unsupported analysis type"):
        await service.analyze(request)

    provider.open.assert_not_awaited()


# -------------------------------------------------------------------
# 4. Provider failure — open raises RasterOpenError
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_raster_open_error():
    metadata = make_raster_metadata(band_count=2)
    provider = make_mock_provider(metadata)
    provider.open = AsyncMock(side_effect=Exception("Connection refused"))
    service = make_service(provider)

    request = make_request()

    with pytest.raises(RasterOpenError, match="Could not open scene"):
        await service.analyze(request)


# -------------------------------------------------------------------
# 5. Resource cleanup — provider always closed even on failure
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resource_cleanup_on_error():
    metadata = make_raster_metadata(band_count=2)
    provider = make_mock_provider(metadata)
    provider.read_band = AsyncMock(side_effect=Exception("I/O failure"))
    service = make_service(provider)

    request = make_request()

    with pytest.raises(ProviderError):
        await service.analyze(request)

    # __aexit__ must have been called — ensures cleanup
    provider.__aexit__.assert_awaited_once()


# -------------------------------------------------------------------
# 6. Statistics failure — statistics engine raises
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_statistics_failure():
    metadata = make_raster_metadata(band_count=2)
    provider = make_mock_provider(metadata)

    registry = IndexRegistry()
    registry.register(NDVIIndex())
    stats_engine = MagicMock(spec=StatisticsEngine)
    stats_engine.compute_statistics.side_effect = Exception("Stats crashed")

    service = AnalysisService(provider, registry, stats_engine)
    request = make_request()

    with pytest.raises(StatisticsError, match="Statistics computation failed"):
        await service.analyze(request)


# -------------------------------------------------------------------
# 7. Band count mismatch
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_insufficient_bands():
    # NDVI needs NIR + RED (2 bands) but raster only has 1
    metadata = make_raster_metadata(band_count=1)
    provider = make_mock_provider(metadata)
    service = make_service(provider)

    request = make_request(AnalysisType.NDVI)

    with pytest.raises(AnalysisValidationError, match="band"):
        await service.analyze(request)


# -------------------------------------------------------------------
# 8. AnalysisResult construction verification
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_result_structure():
    metadata = make_raster_metadata(band_count=2)
    provider = make_mock_provider(metadata)
    stats = make_statistics_summary()
    service = make_service(provider, stats_summary=stats)

    request = make_request()
    result = await service.analyze(request)

    assert result.request == request
    assert result.raster_metadata == metadata
    assert result.statistics == stats
    assert result.processing_status == ProcessingStatus.COMPLETED
    assert result.completed_at >= result.created_at
