from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from src.db.session import AsyncSessionLocal
from src.services.project_service import ProjectService
from src.services.region_service import RegionService
from src.unit_of_work import UnitOfWork


async def get_uow() -> AsyncGenerator[UnitOfWork, None]:
    """Dependency provider for UnitOfWork."""
    yield UnitOfWork(AsyncSessionLocal)


def get_project_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> ProjectService:
    """Dependency provider for ProjectService."""
    return ProjectService(uow)


def get_region_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> RegionService:
    """Dependency provider for RegionService."""
    return RegionService(uow)
