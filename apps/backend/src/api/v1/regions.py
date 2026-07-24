import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_region_service
from src.schemas.region import RegionCreate, RegionRead
from src.schemas.responses import SuccessResponse
from src.services.region_service import RegionService

# Regions belong to projects, nested routing
router = APIRouter(prefix="/projects/{project_id}/regions", tags=["regions"])


@router.post(
    "", response_model=SuccessResponse[RegionRead], status_code=status.HTTP_201_CREATED
)
async def create_region(
    project_id: uuid.UUID,
    data: RegionCreate,
    service: Annotated[RegionService, Depends(get_region_service)],
) -> SuccessResponse[RegionRead]:
    region = await service.create_region(project_id, data)
    return SuccessResponse(data=region)


@router.get("", response_model=SuccessResponse[list[RegionRead]])
async def list_regions(
    project_id: uuid.UUID,
    service: Annotated[RegionService, Depends(get_region_service)],
) -> SuccessResponse[list[RegionRead]]:
    regions = await service.list_regions(project_id)
    return SuccessResponse(data=list(regions))
