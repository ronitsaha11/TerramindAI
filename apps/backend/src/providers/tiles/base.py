from abc import ABC, abstractmethod

from src.schemas.scenes import TileMetadata, TileTemplateResponse


class TileProvider(ABC):
    """Provider-neutral tile generation contract."""

    @abstractmethod
    async def get_metadata(self, cog_href: str) -> TileMetadata:
        """Return normalized tile metadata for a COG."""

    @abstractmethod
    async def get_template(self, cog_href: str) -> TileTemplateResponse:
        """Return an XYZ tile template for a COG."""
