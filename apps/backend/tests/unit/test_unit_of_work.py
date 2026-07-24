from unittest.mock import AsyncMock, MagicMock

import pytest

from src.unit_of_work import UnitOfWork


@pytest.mark.asyncio
async def test_uow_commits_explicitly():
    session_factory = MagicMock()
    mock_session = AsyncMock()
    session_factory.return_value = mock_session

    async with UnitOfWork(session_factory) as uow:
        await uow.commit()

    mock_session.commit.assert_awaited_once()
    mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_uow_rolls_back_on_exception():
    session_factory = MagicMock()
    mock_session = AsyncMock()
    session_factory.return_value = mock_session

    with pytest.raises(ValueError):
        async with UnitOfWork(session_factory):
            raise ValueError("Simulated business logic error")

    mock_session.rollback.assert_awaited_once()
    mock_session.close.assert_awaited_once()
    mock_session.commit.assert_not_awaited()
