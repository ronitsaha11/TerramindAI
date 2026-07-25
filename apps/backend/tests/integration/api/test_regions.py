import uuid
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.dependencies import get_region_service
from src.core.exceptions import AppException
from src.main import app
from src.schemas.region import RegionRead


@pytest.fixture
def mock_region_service():
    return AsyncMock()


@pytest.fixture
async def async_client(mock_region_service):
    app.dependency_overrides[get_region_service] = lambda: mock_region_service
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_region(async_client, mock_region_service):
    project_id = uuid.uuid4()
    mock_region = RegionRead(
        id=uuid.uuid4(),
        project_id=project_id,
        name="Test Region",
        area_sq_km=100.5,
        created_at=datetime.fromisoformat("2023-01-01T00:00:00Z"),
        updated_at=datetime.fromisoformat("2023-01-01T00:00:00Z"),
        geometry={
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        },
    )
    mock_region_service.create_region.return_value = mock_region

    payload = {
        "name": "Test Region",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        },
    }

    response = await async_client.post(
        f"/api/v1/projects/{project_id}/regions", json=payload
    )

    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Test Region"


@pytest.mark.asyncio
async def test_create_region_rejects_non_polygon_geometry(
    async_client, mock_region_service
):
    response = await async_client.post(
        f"/api/v1/projects/{uuid.uuid4()}/regions",
        json={
            "name": "Point Region",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
        },
    )

    assert response.status_code == 422
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    mock_region_service.create_region.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_region_returns_conflict_for_duplicate_name(
    async_client, mock_region_service
):
    mock_region_service.create_region.side_effect = AppException(
        status_code=409, detail="Region name already exists in this project."
    )

    response = await async_client.post(
        f"/api/v1/projects/{uuid.uuid4()}/regions",
        json={
            "name": "Duplicate",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            },
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "APP_409"
