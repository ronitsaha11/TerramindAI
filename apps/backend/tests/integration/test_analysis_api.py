from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.analytics.exceptions import AnalysisValidationError, RasterOpenError
from src.analytics.models import AnalysisRequest
from src.api.dependencies import get_analysis_service
from src.main import app
from src.services.analysis_service import AnalysisService


# Re-use helpers from unit tests (but simpler, just constructing the payload)
def make_valid_payload() -> dict:
    return {
        "project_id": str(uuid4()),
        "region_id": str(uuid4()),
        "scene_id": "s3://bucket/test.tif",
        "requested_analysis": "ndvi",
        "output_options": {
            "persist_raster": True,
            "generate_thumbnail": True,
            "export_format": "COG",
        },
    }


@pytest.fixture
def mock_analysis_service():
    service = MagicMock(spec=AnalysisService)
    # the analyze method is async, so we need an AsyncMock for it
    service.analyze = AsyncMock()
    return service


@pytest.fixture
async def client(mock_analysis_service):
    # Override the dependency to inject the mock
    app.dependency_overrides[get_analysis_service] = lambda: mock_analysis_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_analyze_success(client, mock_analysis_service):
    # Set up the mock response
    payload = make_valid_payload()
    req = AnalysisRequest(**payload)

    # We don't need a full AnalysisResult for this integration test,
    # just a minimal valid one that FastAPI can serialize.
    mock_result = MagicMock()
    # To make Pydantic serialization happy, we mock model_dump()
    mock_result.model_dump.return_value = {
        "analysis_id": str(uuid4()),
        "request": payload,
        "processing_status": "completed",
        "created_at": "2026-07-25T00:00:00Z",
    }
    # For FastAPI dependency on Pydantic BaseModel attributes if it checks them directly
    mock_analysis_service.analyze.return_value = mock_result

    # Actually we should return a real AnalysisResult so FastAPI doesn't
    # fail on response validation
    from datetime import UTC, datetime

    from src.analytics.enums import ProcessingStatus
    from src.analytics.models import AnalysisResult

    real_result = AnalysisResult(
        analysis_id=uuid4(),
        request=req,
        processing_status=ProcessingStatus.COMPLETED,
        created_at=datetime.now(UTC),
    )
    mock_analysis_service.analyze.return_value = real_result

    response = await client.post("/api/v1/analysis", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["processing_status"] == "completed"
    assert "analysis_id" in data

    mock_analysis_service.analyze.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyze_invalid_payload(client, mock_analysis_service):
    payload = make_valid_payload()
    # Break the payload by missing required scene_id
    del payload["scene_id"]

    response = await client.post("/api/v1/analysis", json=payload)

    # FastAPI Pydantic validation kicks in before the service
    assert response.status_code == 422
    mock_analysis_service.analyze.assert_not_awaited()


@pytest.mark.asyncio
async def test_analyze_raster_not_found(client, mock_analysis_service):
    payload = make_valid_payload()

    # Service throws RasterOpenError
    mock_analysis_service.analyze.side_effect = RasterOpenError("S3 bucket not found")

    response = await client.post("/api/v1/analysis", json=payload)

    # The router should map this to 404
    assert response.status_code == 404
    assert "S3 bucket not found" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_analyze_validation_error(client, mock_analysis_service):
    payload = make_valid_payload()

    # Service throws AnalysisValidationError
    mock_analysis_service.analyze.side_effect = AnalysisValidationError(
        "Unsupported index"
    )

    response = await client.post("/api/v1/analysis", json=payload)

    # The router should map this to 400
    assert response.status_code == 400
    assert "Unsupported index" in response.json()["error"]["message"]
