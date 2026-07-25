from collections.abc import Sequence
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import ValidationError

from src.core.exceptions import AppException
from src.providers.catalog.base import CatalogProvider
from src.schemas.scenes import SatelliteSceneRead, STACSearchQuery


class EarthSearchProvider(CatalogProvider):
    """Element84 Earth Search adapter; all STAC parsing remains in this boundary."""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def search(self, query: STACSearchQuery) -> Sequence[SatelliteSceneRead]:
        payload: dict[str, Any] = {
            "collections": query.collections,
            "bbox": query.bbox,
            "limit": query.limit,
        }
        if query.datetime:
            payload["datetime"] = query.datetime
        data = await self._post_search(payload)
        return self._normalize_feature_collection(data)

    async def get_scene(
        self, collection: str, scene_id: str
    ) -> SatelliteSceneRead | None:
        path = "collections/{collection}/items/{scene_id}".format(
            collection=quote(collection, safe=""),
            scene_id=quote(scene_id, safe=""),
        )
        try:
            response = await self.client.get(path)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            raise AppException(
                status_code=504, detail="Satellite catalog timed out."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise self._http_error(exc, "Satellite catalog") from exc
        except httpx.HTTPError as exc:
            raise AppException(
                status_code=503, detail="Satellite catalog is unavailable."
            ) from exc
        except ValueError as exc:
            raise AppException(
                status_code=502, detail="Satellite catalog returned invalid data."
            ) from exc

        try:
            return self._normalize_item(data)
        except (KeyError, TypeError, ValidationError, ValueError) as exc:
            raise AppException(
                status_code=502, detail="Satellite catalog returned invalid data."
            ) from exc

    async def _post_search(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self.client.post("search", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            raise AppException(
                status_code=504, detail="Satellite catalog timed out."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise self._http_error(exc, "Satellite catalog") from exc
        except httpx.HTTPError as exc:
            raise AppException(
                status_code=503, detail="Satellite catalog is unavailable."
            ) from exc
        except ValueError as exc:
            raise AppException(
                status_code=502, detail="Satellite catalog returned invalid data."
            ) from exc

        if not isinstance(data, dict):
            raise AppException(
                status_code=502, detail="Satellite catalog returned invalid data."
            )
        return data

    @staticmethod
    def _http_error(exc: httpx.HTTPStatusError, provider: str) -> AppException:
        if 400 <= exc.response.status_code < 500:
            return AppException(
                status_code=400, detail=f"{provider} rejected the request."
            )
        return AppException(status_code=503, detail=f"{provider} is unavailable.")

    def _normalize_feature_collection(
        self, data: dict[str, Any]
    ) -> list[SatelliteSceneRead]:
        features = data.get("features")
        if not isinstance(features, list):
            raise AppException(
                status_code=502, detail="Satellite catalog returned invalid data."
            )
        try:
            return [self._normalize_item(item) for item in features]
        except (KeyError, TypeError, ValidationError, ValueError) as exc:
            raise AppException(
                status_code=502, detail="Satellite catalog returned invalid data."
            ) from exc

    @staticmethod
    def _normalize_item(item: object) -> SatelliteSceneRead:
        if not isinstance(item, dict):
            raise ValueError("STAC item must be an object")
        properties = item["properties"]
        assets = item.get("assets", {})
        if not isinstance(properties, dict) or not isinstance(assets, dict):
            raise ValueError("STAC item fields are invalid")
        cog_href = EarthSearchProvider._find_cog_href(assets)
        return SatelliteSceneRead(
            id=item["id"],
            collection=item["collection"],
            acquired_at=properties["datetime"],
            bbox=item["bbox"],
            cloud_cover=properties.get("eo:cloud_cover"),
            cog_href=cog_href,
        )

    @staticmethod
    def _find_cog_href(assets: dict[str, Any]) -> str | None:
        for asset in assets.values():
            if not isinstance(asset, dict):
                continue
            href = asset.get("href")
            media_type = asset.get("type", "")
            if isinstance(href, str) and "geotiff" in str(media_type).lower():
                return href
        return None
