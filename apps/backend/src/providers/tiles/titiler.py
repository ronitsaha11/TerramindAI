from typing import Any

import httpx
from pydantic import ValidationError

from src.core.exceptions import AppException
from src.providers.tiles.base import TileProvider
from src.schemas.scenes import TileMetadata, TileTemplateResponse


class TiTilerProvider(TileProvider):
    """TiTiler adapter; TiTiler response details do not escape this class."""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get_metadata(self, cog_href: str) -> TileMetadata:
        data = await self._get("cog/info", cog_href)
        try:
            return TileMetadata(
                bounds=data.get("bounds"),
                minzoom=data.get("minzoom"),
                maxzoom=data.get("maxzoom"),
            )
        except (AttributeError, ValidationError, ValueError) as exc:
            raise AppException(
                status_code=502, detail="Tile provider returned invalid data."
            ) from exc

    async def get_template(self, cog_href: str) -> TileTemplateResponse:
        data = await self._get("cog/WebMercatorQuad/tilejson.json", cog_href)
        try:
            return TileTemplateResponse(
                tiles=data["tiles"],
                minzoom=data.get("minzoom"),
                maxzoom=data.get("maxzoom"),
            )
        except (KeyError, TypeError, ValidationError, ValueError) as exc:
            raise AppException(
                status_code=502, detail="Tile provider returned invalid data."
            ) from exc

    async def _get(self, path: str, cog_href: str) -> dict[str, Any]:
        try:
            response = await self.client.get(path, params={"url": cog_href})
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            raise AppException(
                status_code=504, detail="Tile provider timed out."
            ) from exc
        except httpx.HTTPStatusError as exc:
            if 400 <= exc.response.status_code < 500:
                raise AppException(status_code=400, detail="Invalid COG.") from exc
            raise AppException(
                status_code=503, detail="Tile provider is unavailable."
            ) from exc
        except httpx.HTTPError as exc:
            raise AppException(
                status_code=503, detail="Tile provider is unavailable."
            ) from exc
        except ValueError as exc:
            raise AppException(
                status_code=502, detail="Tile provider returned invalid data."
            ) from exc
        if not isinstance(data, dict):
            raise AppException(
                status_code=502, detail="Tile provider returned invalid data."
            )
        return data
