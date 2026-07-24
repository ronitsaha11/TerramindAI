from types import TracebackType
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.repositories.user_repository import UserRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.region_repository import RegionRepository
from src.repositories.job_repository import JobRepository
from src.repositories.prediction_repository import PredictionRepository
from src.repositories.report_repository import ReportRepository
from src.repositories.audit_log_repository import AuditLogRepository


class UnitOfWork:
    """
    Unit of Work abstraction to coordinate transactions across repositories.
    """
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self.session_factory()
        
        # Repositories share the exact same session, ensuring transaction boundaries.
        self.users = UserRepository(self.session)
        self.projects = ProjectRepository(self.session)
        self.regions = RegionRepository(self.session)
        self.jobs = JobRepository(self.session)
        self.predictions = PredictionRepository(self.session)
        self.reports = ReportRepository(self.session)
        self.audit_logs = AuditLogRepository(self.session)
        
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.session:
            if exc_type is not None:
                await self.rollback()
            await self.session.close()

    async def commit(self) -> None:
        if self.session:
            await self.session.commit()

    async def rollback(self) -> None:
        if self.session:
            await self.session.rollback()
