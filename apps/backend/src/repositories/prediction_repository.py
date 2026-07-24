import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.base import BaseRepository
from src.db.models.prediction import Prediction

class PredictionRepository(BaseRepository[Prediction]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Prediction)

    async def find_by_job(self, job_id: uuid.UUID) -> Sequence[Prediction]:
        result = await self.session.execute(select(Prediction).where(Prediction.job_id == job_id))
        return result.scalars().all()
