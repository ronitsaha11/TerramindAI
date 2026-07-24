import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.base import BaseRepository
from src.db.models.region import Region

class RegionRepository(BaseRepository[Region]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Region)

    async def find_by_project(self, project_id: uuid.UUID) -> Sequence[Region]:
        result = await self.session.execute(select(Region).where(Region.project_id == project_id))
        return result.scalars().all()
