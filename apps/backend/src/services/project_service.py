import uuid
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError

from src.core.exceptions import AppException
from src.db.models.project import Project
from src.schemas.project import ProjectCreate, ProjectRead
from src.services.conflicts import is_unique_violation
from src.unit_of_work import UnitOfWork

# Until authentication is implemented, the initial migration seeds this local-only
# development account. It is intentionally resolved by email instead of assuming a
# foreign-key UUID exists.
DEVELOPMENT_OWNER_EMAIL = "development@terramind.local"


class ProjectService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_project(self, data: ProjectCreate) -> ProjectRead:
        try:
            async with self.uow:
                owner = await self.uow.users.find_by_email(DEVELOPMENT_OWNER_EMAIL)
                if owner is None:
                    raise RuntimeError(
                        "Development owner is missing; run database migrations first."
                    )

                project = Project(
                    owner_id=owner.id, name=data.name, description=data.description
                )

                await self.uow.projects.create(project)
                await self.uow.commit()

                return ProjectRead.model_validate(project)
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise AppException(
                    status_code=409,
                    detail="Project name already exists for this owner.",
                ) from exc
            raise

    async def get_project(self, project_id: uuid.UUID) -> ProjectRead:
        async with self.uow:
            project = await self.uow.projects.get_by_id(project_id)
            if not project:
                raise AppException(status_code=404, detail="Project not found.")
            return ProjectRead.model_validate(project)

    async def list_projects(self) -> Sequence[ProjectRead]:
        async with self.uow:
            owner = await self.uow.users.find_by_email(DEVELOPMENT_OWNER_EMAIL)
            if owner is None:
                raise RuntimeError(
                    "Development owner is missing; run database migrations first."
                )
            projects = await self.uow.projects.find_by_owner(owner.id)
            return [ProjectRead.model_validate(p) for p in projects]
