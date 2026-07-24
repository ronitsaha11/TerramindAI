import uuid
from collections.abc import Sequence

from src.core.exceptions import AppException
from src.db.models.project import Project
from src.schemas.project import ProjectCreate, ProjectRead
from src.unit_of_work import UnitOfWork

# DUMMY USER ID for now, since auth is not implemented
DUMMY_OWNER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class ProjectService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_project(self, data: ProjectCreate) -> ProjectRead:
        async with self.uow:
            existing = await self.uow.projects.find_by_name(data.name)
            if any(p.owner_id == DUMMY_OWNER_ID for p in existing):
                raise AppException(
                    status_code=409,
                    detail="Project name already exists for this owner.",
                )

            project = Project(
                owner_id=DUMMY_OWNER_ID, name=data.name, description=data.description
            )

            await self.uow.projects.create(project)
            await self.uow.commit()

            return ProjectRead.model_validate(project)

    async def get_project(self, project_id: uuid.UUID) -> ProjectRead:
        async with self.uow:
            project = await self.uow.projects.get_by_id(project_id)
            if not project:
                raise AppException(status_code=404, detail="Project not found.")
            return ProjectRead.model_validate(project)

    async def list_projects(self) -> Sequence[ProjectRead]:
        async with self.uow:
            projects = await self.uow.projects.find_by_owner(DUMMY_OWNER_ID)
            return [ProjectRead.model_validate(p) for p in projects]
