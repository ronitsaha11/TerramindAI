import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.ai.exceptions import (
    InferenceExecutionError,
    InferenceValidationError,
    ModelLoadError,
)
from src.ai.models import InferenceResult, PredictionMetadata
from src.api.dependencies import get_ai_inference_service
from src.main import app


@pytest.fixture
def mock_ai_service():
    service = AsyncMock()
    # default successful result
    metadata = PredictionMetadata(
        confidence_score=0.9, execution_time_ms=100.0, model_version="1.0"
    )
    result = InferenceResult(
        request_id=uuid.uuid4(),
        prediction_metadata=metadata,
        result_data={"mask": [[0, 1], [1, 0]]},
    )
    service.execute_inference.return_value = result
    return service


@pytest.fixture
async def async_client(mock_ai_service) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_ai_inference_service] = lambda: mock_ai_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_successful_inference_request(async_client, mock_ai_service):
    payload = {
        "project_id": str(uuid.uuid4()),
        "scene_id": "test_scene",
        "model_id": "test_model",
        "parameters": {"raw_data": [[0, 255]]},
    }

    response = await async_client.post("/api/v1/ai/inference", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["prediction_metadata"]["model_version"] == "1.0"
    assert data["result_data"]["mask"] == [[0, 1], [1, 0]]

    mock_ai_service.execute_inference.assert_called_once()


@pytest.mark.asyncio
async def test_validation_error_mapping_422(async_client, mock_ai_service):
    mock_ai_service.execute_inference.side_effect = InferenceValidationError(
        "Missing raw_data"
    )

    payload = {
        "project_id": str(uuid.uuid4()),
        "scene_id": "test_scene",
        "model_id": "test_model",
        "parameters": {},
    }

    response = await async_client.post("/api/v1/ai/inference", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["message"] == "Missing raw_data"


@pytest.mark.asyncio
async def test_model_load_error_mapping_503(async_client, mock_ai_service):
    mock_ai_service.execute_inference.side_effect = ModelLoadError(
        "Model failed to load"
    )

    payload = {
        "project_id": str(uuid.uuid4()),
        "scene_id": "test_scene",
        "model_id": "test_model",
        "parameters": {},
    }

    response = await async_client.post("/api/v1/ai/inference", json=payload)
    assert response.status_code == 503
    assert response.json()["error"]["message"] == "Model failed to load"


@pytest.mark.asyncio
async def test_inference_execution_error_mapping_500(async_client, mock_ai_service):
    mock_ai_service.execute_inference.side_effect = InferenceExecutionError(
        "Unexpected failure"
    )

    payload = {
        "project_id": str(uuid.uuid4()),
        "scene_id": "test_scene",
        "model_id": "test_model",
        "parameters": {},
    }

    response = await async_client.post("/api/v1/ai/inference", json=payload)
    assert response.status_code == 500
    assert response.json()["error"]["message"] == "Unexpected failure"
