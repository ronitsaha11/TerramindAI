from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from src.api.dependencies import get_catalog_provider, get_tile_provider
from src.core.exceptions import AppException
from src.main import lifespan
from src.providers.catalog.earth_search import EarthSearchProvider
from src.providers.tiles.titiler import TiTilerProvider
from src.schemas.scenes import STACSearchQuery
from src.services.catalog_service import CatalogService
from src.services.tile_service import TileService


def stac_item() -> dict:
    return {
        "id": "scene-1",
        "collection": "sentinel-2-l2a",
        "bbox": [0, 0, 1, 1],
        "properties": {"datetime": "2024-01-01T00:00:00Z", "eo:cloud_cover": 4.0},
        "assets": {
            "visual": {
                "href": "https://example.test/scene.tif",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            }
        },
    }


def stac_item_with_asset_uri(
    asset_uri: str, collection: str = "sentinel-2-l2a"
) -> dict:
    item = stac_item()
    item["collection"] = collection
    item["assets"]["visual"]["href"] = asset_uri
    return item


def mock_client(handler: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=handler, base_url="https://provider.test")


@pytest.mark.asyncio
async def test_earth_search_normalizes_successful_search():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"features": [stac_item()]})
    )
    async with mock_client(transport) as client:
        scenes = await EarthSearchProvider(client).search(
            STACSearchQuery(collections=["sentinel-2-l2a"], bbox=[0, 0, 1, 1])
        )

    assert len(scenes) == 1
    assert scenes[0].id == "scene-1"
    assert str(scenes[0].cog_href) == "https://example.test/scene.tif"


@pytest.mark.asyncio
async def test_earth_search_preserves_non_http_stac_asset_reference():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, json={"features": [stac_item_with_asset_uri("s3://bucket/scene.tif")]}
        )
    )
    async with mock_client(transport) as client:
        scenes = await EarthSearchProvider(client).search(
            STACSearchQuery(collections=["sentinel-2-l2a"], bbox=[0, 0, 1, 1])
        )

    assert scenes[0].cog_href == "s3://bucket/scene.tif"


@pytest.mark.asyncio
async def test_earth_search_timeout_becomes_domain_exception():
    def timeout(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    async with mock_client(httpx.MockTransport(timeout)) as client:
        with pytest.raises(AppException) as exc_info:
            await EarthSearchProvider(client).search(
                STACSearchQuery(collections=["sentinel-2-l2a"], bbox=[0, 0, 1, 1])
            )

    assert exc_info.value.status_code == 504


@pytest.mark.asyncio
async def test_earth_search_rejects_malformed_stac_response():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"features": [{"id": "missing"}]})
    )
    async with mock_client(transport) as client:
        with pytest.raises(AppException) as exc_info:
            await EarthSearchProvider(client).search(
                STACSearchQuery(collections=["sentinel-2-l2a"], bbox=[0, 0, 1, 1])
            )

    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code, expected_status", [(400, 400), (500, 503)])
async def test_earth_search_translates_4xx_and_5xx_responses(
    status_code, expected_status
):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(status_code, request=request)
    )
    async with mock_client(transport) as client:
        with pytest.raises(AppException) as exc_info:
            await EarthSearchProvider(client).search(
                STACSearchQuery(collections=["sentinel-2-l2a"], bbox=[0, 0, 1, 1])
            )

    assert exc_info.value.status_code == expected_status


@pytest.mark.asyncio
async def test_scene_lookup_is_collection_scoped():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json=stac_item_with_asset_uri(
                "https://example.test/scene.tif", "landsat-c2-l2"
            ),
        )

    async with mock_client(httpx.MockTransport(handler)) as client:
        scene = await EarthSearchProvider(client).get_scene(
            "landsat-c2-l2", "shared-id"
        )

    assert scene is not None
    assert scene.collection == "landsat-c2-l2"
    assert requests[0].url.path == "/collections/landsat-c2-l2/items/shared-id"


@pytest.mark.asyncio
async def test_catalog_service_returns_empty_results_without_provider_leakage():
    provider = AsyncMock()
    provider.search.return_value = []

    scenes = await CatalogService(provider).search(
        STACSearchQuery(collections=["sentinel-2-l2a"], bbox=[0, 0, 1, 1])
    )

    assert list(scenes) == []


@pytest.mark.asyncio
async def test_tile_service_rejects_invalid_cog_href():
    provider = AsyncMock()

    with pytest.raises(AppException) as exc_info:
        await TileService(provider).get_template("file:///tmp/scene.tif")

    assert exc_info.value.status_code == 400
    provider.get_template.assert_not_awaited()


@pytest.mark.asyncio
async def test_tile_service_accepts_s3_cog_uri():
    provider = AsyncMock()

    await TileService(provider).get_template("s3://bucket/scene.tif")

    provider.get_template.assert_awaited_once_with("s3://bucket/scene.tif")


@pytest.mark.asyncio
async def test_titiler_generates_tile_template():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "tiles": ["https://tiles.test/cog/WebMercatorQuad/{z}/{x}/{y}.png"],
                "minzoom": 8,
                "maxzoom": 14,
            },
        )
    )
    async with mock_client(transport) as client:
        template = await TiTilerProvider(client).get_template(
            "https://example.test/scene.tif"
        )

    assert template.minzoom == 8
    assert str(template.tiles[0]).endswith("{z}/{x}/{y}.png")


@pytest.mark.asyncio
async def test_lifespan_manages_shared_provider_clients(monkeypatch):
    app = FastAPI()
    monkeypatch.setattr("src.main.redis_client.connect", AsyncMock())
    monkeypatch.setattr("src.main.redis_client.disconnect", AsyncMock())
    monkeypatch.setattr("src.main.engine.dispose", AsyncMock())

    async with lifespan(app):
        request = SimpleNamespace(app=app)
        catalog_provider = get_catalog_provider(request)
        tile_provider = get_tile_provider(request)

        assert catalog_provider.client is app.state.earth_search_client
        assert tile_provider.client is app.state.titiler_client
        assert not app.state.earth_search_client.is_closed
        assert not app.state.titiler_client.is_closed

    assert app.state.earth_search_client.is_closed
    assert app.state.titiler_client.is_closed


# --- New tests for Milestone 6 architecture review fixes ---


@pytest.mark.asyncio
async def test_earth_search_get_scene_returns_none_on_404():
    """Upstream 404 must be translated to None, not raised as an exception."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(404, request=request)
    )
    async with mock_client(transport) as client:
        result = await EarthSearchProvider(client).get_scene(
            "sentinel-2-l2a", "nonexistent"
        )

    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code, expected_status", [(400, 400), (500, 503)])
async def test_earth_search_get_scene_translates_4xx_and_5xx(
    status_code, expected_status
):
    """get_scene must distinguish client-rejected (4xx->400) from outage (5xx->503)."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(status_code, request=request)
    )
    async with mock_client(transport) as client:
        with pytest.raises(AppException) as exc_info:
            await EarthSearchProvider(client).get_scene(
                "sentinel-2-l2a", "scene-1"
            )

    assert exc_info.value.status_code == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code, expected_status", [(400, 400), (500, 503)])
async def test_titiler_translates_4xx_and_5xx_responses(
    status_code, expected_status
):
    """TiTiler adapter must map upstream 4xx->400 and 5xx->503."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(status_code, request=request)
    )
    async with mock_client(transport) as client:
        with pytest.raises(AppException) as exc_info:
            await TiTilerProvider(client).get_template(
                "https://example.test/scene.tif"
            )

    assert exc_info.value.status_code == expected_status


@pytest.mark.asyncio
async def test_titiler_timeout_becomes_domain_exception():
    """TiTiler timeout must surface as 504, not leak a transport exception."""
    def timeout(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    async with mock_client(httpx.MockTransport(timeout)) as client:
        with pytest.raises(AppException) as exc_info:
            await TiTilerProvider(client).get_template(
                "https://example.test/scene.tif"
            )

    assert exc_info.value.status_code == 504


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_uri", [
    "file:///tmp/scene.tif",
    "/absolute/path/scene.tif",
    "relative/path.tif",
    "ftp://server/scene.tif",
])
async def test_tile_service_rejects_non_routable_uri(bad_uri):
    """TileService must reject URI schemes that are not routable by tile providers."""
    provider = AsyncMock()

    with pytest.raises(AppException) as exc_info:
        await TileService(provider).get_template(bad_uri)

    assert exc_info.value.status_code == 400
    provider.get_template.assert_not_awaited()
