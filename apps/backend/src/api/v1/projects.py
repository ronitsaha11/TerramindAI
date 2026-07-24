import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_project_service
from src.schemas.project import ProjectCreate, ProjectRead
from src.schemas.responses import SuccessResponse
from src.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "", response_model=SuccessResponse[ProjectRead], status_code=status.HTTP_201_CREATED
)
async def create_project(
    data: ProjectCreate,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> SuccessResponse[ProjectRead]:
    project = await service.create_project(data)
    return SuccessResponse(data=project)


@router.get("", response_model=SuccessResponse[list[ProjectRead]])
async def list_projects(
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> SuccessResponse[list[ProjectRead]]:
    projects = await service.list_projects()
    return SuccessResponse(data=projects)


@router.get("/{project_id}", response_model=SuccessResponse[ProjectRead])
async def get_project(
    project_id: uuid.UUID,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> SuccessResponse[ProjectRead]:
    project = await service.get_project(project_id)
    return SuccessResponse(data=project)
