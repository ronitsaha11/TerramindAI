from unittest.mock import AsyncMock, MagicMock

import pytest

from src.db.models.user import User
from src.repositories.user_repository import UserRepository


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.mark.asyncio
async def test_find_by_email(mock_session):
    repo = UserRepository(mock_session)
    email = "test@example.com"

    mock_result = MagicMock()
    mock_user = User(email=email, name="Test User")
    mock_result.scalars().first.return_value = mock_user
    mock_session.execute.return_value = mock_result

    result = await repo.find_by_email(email)

    mock_session.execute.assert_awaited_once()
    assert result is mock_user
