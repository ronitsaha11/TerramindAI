import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.report import Report
from src.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Report)

    async def find_by_prediction(self, prediction_id: uuid.UUID) -> Sequence[Report]:
        result = await self.session.execute(
            select(Report).where(Report.prediction_id == prediction_id)
        )
        return result.scalars().all()
