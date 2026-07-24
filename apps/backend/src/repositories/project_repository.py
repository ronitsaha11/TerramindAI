import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.base import BaseRepository
from src.db.models.project import Project

class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Project)

    async def find_by_owner(self, owner_id: uuid.UUID) -> Sequence[Project]:
        result = await self.session.execute(select(Project).where(Project.owner_id == owner_id))
        return result.scalars().all()

    async def find_by_name(self, name: str) -> Sequence[Project]:
        result = await self.session.execute(select(Project).where(Project.name == name))
        return result.scalars().all()
