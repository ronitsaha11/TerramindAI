from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.schemas.scenes import SatelliteSceneRead, STACSearchQuery


class CatalogProvider(ABC):
    """Provider-neutral satellite catalog contract."""

    @abstractmethod
    async def search(self, query: STACSearchQuery) -> Sequence[SatelliteSceneRead]:
        """Search and normalize catalog scenes."""

    @abstractmethod
    async def get_scene(
        self, collection: str, scene_id: str
    ) -> SatelliteSceneRead | None:
        """Fetch one normalized STAC Item identified by collection and item ID."""
