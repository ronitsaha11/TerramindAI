from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_catalog_service, get_tile_service
from src.schemas.responses import SuccessResponse
from src.schemas.scenes import (
    SatelliteSceneRead,
    STACSearchQuery,
    TileTemplateResponse,
)
from src.services.catalog_service import CatalogService
from src.services.tile_service import TileService

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.post("/search", response_model=SuccessResponse[list[SatelliteSceneRead]])
async def search_scenes(
    query: STACSearchQuery,
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> SuccessResponse[list[SatelliteSceneRead]]:
    return SuccessResponse(data=list(await service.search(query)))


@router.get("/tile-json", response_model=SuccessResponse[TileTemplateResponse])
async def get_tile_template(
    cog_href: Annotated[
        str, Query(description="Cloud Optimized GeoTIFF URI (https://, s3://)")
    ],
    service: Annotated[TileService, Depends(get_tile_service)],
) -> SuccessResponse[TileTemplateResponse]:
    return SuccessResponse(data=await service.get_template(cog_href))


@router.get("/{scene_id}", response_model=SuccessResponse[SatelliteSceneRead])
async def get_scene(
    scene_id: str,
    collection: Annotated[str, Query(min_length=1)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> SuccessResponse[SatelliteSceneRead]:
    return SuccessResponse(data=await service.get_scene(collection, scene_id))
