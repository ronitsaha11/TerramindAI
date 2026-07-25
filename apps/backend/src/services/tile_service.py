from urllib.parse import urlparse

from src.core.exceptions import AppException
from src.providers.tiles.base import TileProvider
from src.schemas.scenes import TileMetadata, TileTemplateResponse


class TileService:
    """Application service for provider-neutral COG tile discovery."""

    def __init__(self, provider: TileProvider):
        self.provider = provider

    async def get_metadata(self, cog_href: str) -> TileMetadata:
        return await self.provider.get_metadata(self._validate_cog_href(cog_href))

    async def get_template(self, cog_href: str) -> TileTemplateResponse:
        return await self.provider.get_template(self._validate_cog_href(cog_href))

    @staticmethod
    def _validate_cog_href(cog_href: str) -> str:
        parsed = urlparse(cog_href)
        if parsed.scheme not in {"http", "https", "s3"} or not parsed.netloc:
            raise AppException(
                status_code=400,
                detail="A valid HTTP(S) or S3 COG URI is required.",
            )
        return cog_href
