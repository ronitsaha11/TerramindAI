import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from src.core.exceptions import AppException
from src.schemas.project import ProjectCreate
from src.schemas.region import RegionCreate
from src.services.project_service import ProjectService
from src.services.region_service import RegionService


class UniqueViolation(Exception):
    sqlstate = "23505"


class StubUnitOfWork:
    def __init__(self) -> None:
        self.users = SimpleNamespace(find_by_email=AsyncMock())
        self.projects = SimpleNamespace(get_by_id=AsyncMock(), create=AsyncMock())
        self.regions = SimpleNamespace(create=AsyncMock())
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()


def unique_constraint_error() -> IntegrityError:
    return IntegrityError("INSERT", {}, UniqueViolation())


@pytest.mark.asyncio
async def test_project_service_maps_unique_constraint_to_conflict():
    uow = StubUnitOfWork()
    uow.users.find_by_email.return_value = SimpleNamespace(id=uuid.uuid4())
    uow.projects.create.side_effect = unique_constraint_error()

    with pytest.raises(AppException) as exc_info:
        await ProjectService(uow).create_project(ProjectCreate(name="Duplicate"))

    assert exc_info.value.status_code == 409
    uow.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_region_service_maps_unique_constraint_to_conflict():
    uow = StubUnitOfWork()
    uow.projects.get_by_id.return_value = SimpleNamespace(id=uuid.uuid4())
    uow.regions.create.side_effect = unique_constraint_error()
    region = RegionCreate(
        name="Duplicate",
        geometry={
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        },
    )

    with pytest.raises(AppException) as exc_info:
        await RegionService(uow).create_region(uuid.uuid4(), region)

    assert exc_info.value.status_code == 409
    uow.rollback.assert_awaited_once()
