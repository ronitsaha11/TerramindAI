import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.analytics.enums import AnalysisType, ProcessingStatus
from src.analytics.models import (
    AnalysisRequest,
    AnalysisResult,
    BandInfo,
    OutputOptions,
    RasterMetadata,
)
from src.analytics.types import (
    BandIdentifier,
    BoundingBox,
    CoordinateReferenceSystem,
    GeoTransform,
    RasterResolution,
)


def test_band_info() -> None:
    band = BandInfo(
        identifier=BandIdentifier("B04"),
        name="Red",
        common_name="red",
        description="Visible Red",
        nodata_value=0.0,
    )
    assert band.identifier == "B04"
    assert band.common_name == "red"


def test_raster_metadata() -> None:
    metadata = RasterMetadata(
        crs=CoordinateReferenceSystem("EPSG:32610"),
        bounds=BoundingBox(west=-120, south=30, east=-119, north=31),
        resolution=RasterResolution(x=10, y=10),
        transform=GeoTransform(a=10, b=0, c=500000, d=0, e=-10, f=4000000),
        bands=[BandInfo(identifier=BandIdentifier("B04"))],
        width=10980,
        height=10980,
    )
    assert metadata.width == 10980
    assert len(metadata.bands) == 1


def test_analysis_request() -> None:
    req = AnalysisRequest(
        project_id=uuid.uuid4(),
        region_id=uuid.uuid4(),
        scene_id="S2A_12345",
        requested_analysis=AnalysisType.NDVI,
        selected_bands=[BandIdentifier("B04"), BandIdentifier("B08")],
        output_options=OutputOptions(persist_raster=True),
    )
    assert req.requested_analysis == AnalysisType.NDVI
    assert req.selected_bands == ["B04", "B08"]
    assert req.output_options.persist_raster is True


def test_analysis_result() -> None:
    req = AnalysisRequest(
        project_id=uuid.uuid4(),
        region_id=uuid.uuid4(),
        scene_id="S2A_12345",
        requested_analysis=AnalysisType.NDVI,
    )
    result = AnalysisResult(
        analysis_id=uuid.uuid4(),
        request=req,
        processing_status=ProcessingStatus.COMPLETED,
        created_at=datetime.now(UTC),
    )
    assert result.processing_status == ProcessingStatus.COMPLETED
    assert result.request.scene_id == "S2A_12345"


def test_analysis_request_invalid_enum() -> None:
    with pytest.raises(ValidationError):
        AnalysisRequest(
            project_id=uuid.uuid4(),
            region_id=uuid.uuid4(),
            scene_id="S2A_12345",
            requested_analysis="invalid_analysis",  # type: ignore
        )
