import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.repositories.project_repository import ProjectRepository
from src.db.models.project import Project

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_find_by_owner(mock_session):
    repo = ProjectRepository(mock_session)
    owner_id = uuid.uuid4()
    
    mock_result = MagicMock()
    mock_project = Project(name="Test", owner_id=owner_id)
    mock_result.scalars().all.return_value = [mock_project]
    mock_session.execute.return_value = mock_result
    
    result = await repo.find_by_owner(owner_id)
    
    mock_session.execute.assert_awaited_once()
    assert result == [mock_project]
