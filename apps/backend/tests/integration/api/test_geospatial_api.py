from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.dependencies import get_geospatial_service
from src.geospatial.exceptions import GeospatialExecutionError
from src.geospatial.models import GeoJSONExportResult
from src.main import app


@pytest.fixture
def mock_geospatial_service():
    service = MagicMock()
    # Provide a mock return value
    mock_result = GeoJSONExportResult(
        feature_collection={
            "type": "FeatureCollection",
            "features": [],
            "metadata": {"test": "metadata"},
        },
        export_metadata={"feature_count": 0},
        export_duration_ms=5.0,
    )
    service.process_mask.return_value = mock_result
    return service


@pytest.fixture
async def async_client(mock_geospatial_service) -> AsyncClient:
    app.dependency_overrides[get_geospatial_service] = lambda: mock_geospatial_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_successful_vectorization(
    async_client: AsyncClient, mock_geospatial_service: MagicMock
):
    payload = {
        "mask": [[0, 1], [1, 0]],
        "transform": [1.0, 0.0, 0.0, 0.0, -1.0, 10.0],
        "crs": "EPSG:4326",
    }

    response = await async_client.post("/api/v1/geospatial/vectorize", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["feature_collection"]["type"] == "FeatureCollection"
    assert data["export_duration_ms"] == 5.0

    mock_geospatial_service.process_mask.assert_called_once()


@pytest.mark.asyncio
async def test_validation_errors(async_client: AsyncClient):
    payload = {
        "mask": [[0, 1]],
        # Missing transform and crs
    }

    response = await async_client.post("/api/v1/geospatial/vectorize", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_geospatial_execution_error_mapping_500(
    async_client: AsyncClient, mock_geospatial_service: MagicMock
):
    mock_geospatial_service.process_mask.side_effect = GeospatialExecutionError(
        "Geospatial pipeline failed"
    )

    payload = {
        "mask": [[0, 1], [1, 0]],
        "transform": [1.0, 0.0, 0.0, 0.0, -1.0, 10.0],
        "crs": "EPSG:4326",
    }

    response = await async_client.post("/api/v1/geospatial/vectorize", json=payload)
    assert response.status_code == 500
    assert "Geospatial pipeline failed" in response.json()["error"]["message"]
