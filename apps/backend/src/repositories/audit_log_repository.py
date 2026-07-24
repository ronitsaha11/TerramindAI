from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.base import BaseRepository
from src.db.models.audit_log import AuditLog

class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AuditLog)

    async def find_recent(self, limit: int = 50) -> Sequence[AuditLog]:
        result = await self.session.execute(
            select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
        )
        return result.scalars().all()
