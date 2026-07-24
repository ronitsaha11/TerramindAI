from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.enums import JobStatus
from src.db.models.job import Job
from src.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Job)

    async def find_by_status(self, status: JobStatus) -> Sequence[Job]:
        result = await self.session.execute(select(Job).where(Job.status == status))
        return result.scalars().all()

    async def find_running_jobs(self) -> Sequence[Job]:
        return await self.find_by_status(JobStatus.RUNNING)
