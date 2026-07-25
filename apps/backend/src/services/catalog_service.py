from collections.abc import Sequence

from src.core.exceptions import AppException
from src.providers.catalog.base import CatalogProvider
from src.schemas.scenes import SatelliteSceneRead, STACSearchQuery


class CatalogService:
    """Application service for normalized satellite catalog discovery."""

    def __init__(self, provider: CatalogProvider):
        self.provider = provider

    async def search(self, query: STACSearchQuery) -> Sequence[SatelliteSceneRead]:
        return await self.provider.search(query)

    async def get_scene(self, collection: str, scene_id: str) -> SatelliteSceneRead:
        scene = await self.provider.get_scene(collection, scene_id)
        if scene is None:
            raise AppException(status_code=404, detail="Satellite scene not found.")
        return scene
