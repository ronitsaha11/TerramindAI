import uuid
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.dependencies import get_project_service
from src.core.exceptions import AppException
from src.db.models.enums import ProjectStatus
from src.main import app
from src.schemas.project import ProjectRead


@pytest.fixture
def mock_project_service():
    return AsyncMock()


@pytest.fixture
async def async_client(mock_project_service):
    app.dependency_overrides[get_project_service] = lambda: mock_project_service
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_project(async_client, mock_project_service):
    mock_project = ProjectRead(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        name="Test Project",
        description="A test",
        status=ProjectStatus.ACTIVE,
        created_at=datetime.fromisoformat("2023-01-01T00:00:00"),
        updated_at=datetime.fromisoformat("2023-01-01T00:00:00"),
    )
    mock_project_service.create_project.return_value = mock_project

    response = await async_client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": "A test"}
    )

    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Test Project"
    assert response.json()["data"]["id"] == str(mock_project.id)


@pytest.mark.asyncio
async def test_create_project_returns_conflict_for_duplicate_name(
    async_client, mock_project_service
):
    mock_project_service.create_project.side_effect = AppException(
        status_code=409, detail="Project name already exists for this owner."
    )

    response = await async_client.post("/api/v1/projects", json={"name": "Duplicate"})

    assert response.status_code == 409
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "APP_409"
