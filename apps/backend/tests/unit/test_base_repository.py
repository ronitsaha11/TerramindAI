import uuid
import pytest
from unittest.mock import AsyncMock
from src.repositories.base import BaseRepository

class DummyModel:
    pass

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_base_repo_create(mock_session):
    repo = BaseRepository(mock_session, DummyModel)
    obj = DummyModel()
    
    result = await repo.create(obj)
    
    mock_session.add.assert_called_once_with(obj)
    mock_session.flush.assert_awaited_once()
    # Ensure commit is never called!
    mock_session.commit.assert_not_called()
    assert result is obj

@pytest.mark.asyncio
async def test_base_repo_get_by_id(mock_session):
    repo = BaseRepository(mock_session, DummyModel)
    obj_id = uuid.uuid4()
    
    expected_obj = DummyModel()
    mock_session.get.return_value = expected_obj
    
    result = await repo.get_by_id(obj_id)
    
    mock_session.get.assert_awaited_once_with(DummyModel, obj_id)
    assert result is expected_obj

@pytest.mark.asyncio
async def test_base_repo_delete(mock_session):
    repo = BaseRepository(mock_session, DummyModel)
    obj = DummyModel()
    
    await repo.delete(obj)
    
    mock_session.delete.assert_awaited_once_with(obj)
    mock_session.flush.assert_awaited_once()
    mock_session.commit.assert_not_called()
