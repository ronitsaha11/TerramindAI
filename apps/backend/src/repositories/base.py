import uuid
from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic Base Repository handling persistence operations.
    Never calls session.commit(). Leaves transaction boundaries to the UnitOfWork.
    """

    def __init__(self, session: AsyncSession, model_cls: type[ModelType]):
        self.session = session
        self.model_cls = model_cls

    async def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_by_id(self, id: uuid.UUID | tuple) -> ModelType | None:
        return await self.session.get(self.model_cls, id)

    async def list(self) -> Sequence[ModelType]:
        result = await self.session.execute(select(self.model_cls))
        return result.scalars().all()

    async def exists(self, id: uuid.UUID | tuple) -> bool:
        obj = await self.get_by_id(id)
        return obj is not None

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(self.model_cls)
        )
        return result.scalar_one()

    async def update(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def paginate(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        result = await self.session.execute(
            select(self.model_cls).offset(skip).limit(limit)
        )
        return result.scalars().all()
