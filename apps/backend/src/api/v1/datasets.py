import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile, status

from src.api.dependencies import get_dataset_service
from src.schemas.dataset import DatasetRead
from src.schemas.responses import SuccessResponse
from src.services.dataset_service import DatasetService

router = APIRouter(prefix="/projects/{project_id}/datasets", tags=["datasets"])


@router.post(
    "",
    response_model=SuccessResponse[DatasetRead],
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    project_id: uuid.UUID,
    file: UploadFile,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> SuccessResponse[DatasetRead]:
    content = await file.read()
    dataset = await service.create_dataset_from_geojson(
        project_id=project_id,
        filename=file.filename or "untitled.geojson",
        geojson_content=content,
    )
    return SuccessResponse(data=dataset)


@router.get("", response_model=SuccessResponse[list[DatasetRead]])
async def list_datasets(
    project_id: uuid.UUID,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> SuccessResponse[list[DatasetRead]]:
    datasets = await service.list_datasets(project_id)
    return SuccessResponse(data=list(datasets))


@router.get("/{dataset_id}/geojson")
async def get_dataset_geojson(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict:
    return await service.get_dataset_geojson(project_id, dataset_id)


@router.get("/{dataset_id}/query/nearby")
async def query_nearby(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    lon: Annotated[float, Query(description="Longitude of the query point")],
    lat: Annotated[float, Query(description="Latitude of the query point")],
    radius_meters: Annotated[float, Query(gt=0, description="Search radius in meters")],
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict:
    return await service.query_nearby(
        project_id=project_id,
        dataset_id=dataset_id,
        lon=lon,
        lat=lat,
        radius_meters=radius_meters,
    )


@router.get("/{dataset_id}/query/contains")
async def query_contains(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    feature_id: Annotated[
        uuid.UUID,
        Query(description="ID of the polygon feature to test containment against"),
    ],
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict:
    return await service.query_contains(
        project_id=project_id,
        dataset_id=dataset_id,
        feature_id=feature_id,
    )


@router.get("/{dataset_id}/query/intersects")
async def query_intersects(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    feature_id: Annotated[
        uuid.UUID, Query(description="ID of the feature to test intersection against")
    ],
    target_dataset_id: Annotated[
        uuid.UUID,
        Query(description="ID of the dataset to search for intersecting features"),
    ],
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> dict:
    return await service.query_intersects(
        project_id=project_id,
        dataset_id=dataset_id,
        feature_id=feature_id,
        target_dataset_id=target_dataset_id,
    )
