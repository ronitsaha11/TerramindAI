import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.db.models.region import Region
from src.repositories.region_repository import RegionRepository


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.mark.asyncio
async def test_find_by_project(mock_session):
    repo = RegionRepository(mock_session)
    project_id = uuid.uuid4()

    mock_result = MagicMock()
    mock_region = Region(
        name="Region A",
        project_id=project_id,
        geometry="POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))",
    )
    mock_result.scalars().all.return_value = [mock_region]
    mock_session.execute.return_value = mock_result

    result = await repo.find_by_project(project_id)

    mock_session.execute.assert_awaited_once()
    assert result == [mock_region]
