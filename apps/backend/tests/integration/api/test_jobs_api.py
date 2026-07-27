import datetime
import uuid
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import httpx
import pytest
from httpx import ASGITransport

from src.api.dependencies import get_job_service
from src.async_processing.enums import JobStatus
from src.async_processing.exceptions import (
    InvalidJobOperationError,
    JobCancellationError,
    JobNotFoundError,
    JobRetryError,
)
from src.async_processing.models import JobProgress, JobRecord
from src.async_processing.service import JobService
from src.main import app


@pytest.fixture
def mock_job_service() -> MagicMock:
    return MagicMock(spec=JobService)


@pytest.fixture
def override_get_job_service(mock_job_service: MagicMock) -> None:
    app.dependency_overrides[get_job_service] = lambda: mock_job_service
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(
    override_get_job_service: None,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_submit_ai_inference(
    async_client: httpx.AsyncClient, mock_job_service: MagicMock
) -> None:
    job_id = uuid.uuid4()
    mock_job_service.submit_ai_inference.return_value = job_id
    payload = {"data": 123}

    response = await async_client.post("/api/v1/jobs/ai/inference", json=payload)

    assert response.status_code == 202
    data = response.json()
    assert data["job_id"] == str(job_id)
    assert data["status"] == JobStatus.PENDING
    mock_job_service.submit_ai_inference.assert_called_once_with(payload)


@pytest.mark.asyncio
async def test_submit_geospatial_vectorization(
    async_client: httpx.AsyncClient, mock_job_service: MagicMock
) -> None:
    job_id = uuid.uuid4()
    mock_job_service.submit_geospatial_vectorization.return_value = job_id
    payload = {"geo": "spatial"}

    response = await async_client.post(
        "/api/v1/jobs/geospatial/vectorize", json=payload
    )

    assert response.status_code == 202
    data = response.json()
    assert data["job_id"] == str(job_id)
    assert data["status"] == JobStatus.PENDING
    mock_job_service.submit_geospatial_vectorization.assert_called_once_with(payload)


@pytest.mark.asyncio
async def test_get_job(
    async_client: httpx.AsyncClient, mock_job_service: MagicMock
) -> None:
    job_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.UTC)
    mock_job = JobRecord(
        job_id=job_id,
        task_name="test",
        status=JobStatus.SUCCESS,
        created_at=now,
        updated_at=now,
    )
    mock_job_service.get_job.return_value = mock_job

    response = await async_client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["job_id"] == str(job_id)
    mock_job_service.get_job.assert_called_once_with(job_id)


@pytest.mark.asyncio
async def test_get_job_status(
    async_client: httpx.AsyncClient, mock_job_service: MagicMock
) -> None:
    job_id = uuid.uuid4()
    mock_job_service.get_job_status.return_value = JobStatus.PROCESSING

    response = await async_client.get(f"/api/v1/jobs/{job_id}/status")

    assert response.status_code == 200
    assert response.json() == {"job_id": str(job_id), "status": JobStatus.PROCESSING}


@pytest.mark.asyncio
async def test_get_job_progress(
    async_client: httpx.AsyncClient, mock_job_service: MagicMock
) -> None:
    job_id = uuid.uuid4()
    progress = JobProgress(percentage=50.0, current_step=1, total_steps=2)
    mock_job_service.get_job_progress.return_value = progress

    response = await async_client.get(f"/api/v1/jobs/{job_id}/progress")

    assert response.status_code == 200
    assert response.json()["percentage"] == 50.0


@pytest.mark.asyncio
async def test_get_job_result_success(
    async_client: httpx.AsyncClient, mock_job_service: MagicMock
) -> None:
    job_id = uuid.uuid4()
    mock_job_service.get_job_result.return_value = "s3://test/1.json"

    response = await async_client.get(f"/api/v1/jobs/{job_id}/result")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": str(job_id),
        "result_reference": "s3://test/1.json",
    }


@pytest.mark.asyncio
async def test_get_job_result_incomplete(
    async_client: httpx.AsyncClient, mock_job_service: MagicMock
) -> None:
    job_id = uuid.uuid4()
    mock_job_service.get_job_result.side_effect = InvalidJobOperationError(
        "Not complete"
    )

    response = await async_client.get(f"/api/v1/jobs/{job_id}/result")

    assert response.status_code == 409
    assert "Not complete" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_cancel_job(
    async_client: httpx.AsyncClient, mock_job_service: MagicMock
) -> None:
    job_id = uuid.uuid4()

    response = await async_client.delete(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 204
    mock_job_service.cancel_job.assert_called_once_with(job_id)


@pytest.mark.asyncio
async def test_cancel_job_terminal(
    async_client: httpx.AsyncClient, mock_job_service: MagicMock
) -> None:
    job_id = uuid.uuid4()
    mock_job_service.cancel_job.side_effect = JobCancellationError("terminal state")

    response = await async_client.delete(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 409
    assert "terminal state" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_retry_job(
    async_client: httpx.AsyncClient, mock_job_service: MagicMock
) -> None:
    job_id = uuid.uuid4()

    response = await async_client.post(f"/api/v1/jobs/{job_id}/retry")

    assert response.status_code == 202
    assert response.json()["job_id"] == str(job_id)
    assert response.json()["status"] == JobStatus.RETRY


@pytest.mark.asyncio
async def test_retry_job_invalid(
    async_client: httpx.AsyncClient, mock_job_service: MagicMock
) -> None:
    job_id = uuid.uuid4()
    mock_job_service.retry_job.side_effect = JobRetryError("already completed")

    response = await async_client.post(f"/api/v1/jobs/{job_id}/retry")

    assert response.status_code == 409
    assert "already completed" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_list_jobs(
    async_client: httpx.AsyncClient, mock_job_service: MagicMock
) -> None:
    now = datetime.datetime.now(datetime.UTC)
    mock_jobs = [
        JobRecord(
            job_id=uuid.uuid4(),
            task_name="test1",
            status=JobStatus.SUCCESS,
            created_at=now,
            updated_at=now,
        ),
        JobRecord(
            job_id=uuid.uuid4(),
            task_name="test2",
            status=JobStatus.PENDING,
            created_at=now,
            updated_at=now,
        ),
    ]
    mock_job_service.list_jobs.return_value = mock_jobs

    response = await async_client.get("/api/v1/jobs")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["task_name"] == "test1"


@pytest.mark.asyncio
async def test_unknown_job(
    async_client: httpx.AsyncClient, mock_job_service: MagicMock
) -> None:
    job_id = uuid.uuid4()
    mock_job_service.get_job.side_effect = JobNotFoundError("Not found")

    response = await async_client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 404
