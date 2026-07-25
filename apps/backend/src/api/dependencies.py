from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request

from src.analytics.engine import AnalyticsEngine
from src.analytics.indices import default_registry as default_index_registry
from src.analytics.providers.base import RasterProvider
from src.analytics.providers.cog_provider import COGRasterProvider
from src.analytics.statistics import default_engine as default_statistics_engine
from src.db.session import AsyncSessionLocal
from src.providers.catalog.base import CatalogProvider
from src.providers.catalog.earth_search import EarthSearchProvider
from src.providers.tiles.base import TileProvider
from src.providers.tiles.titiler import TiTilerProvider
from src.services.analysis_service import AnalysisService
from src.services.catalog_service import CatalogService
from src.services.project_service import ProjectService
from src.services.region_service import RegionService
from src.services.tile_service import TileService
from src.unit_of_work import UnitOfWork


async def get_uow() -> AsyncGenerator[UnitOfWork, None]:
    """Dependency provider for UnitOfWork."""
    yield UnitOfWork(AsyncSessionLocal)


def get_project_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> ProjectService:
    """Dependency provider for ProjectService."""
    return ProjectService(uow)


def get_region_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> RegionService:
    """Dependency provider for RegionService."""
    return RegionService(uow)


def get_catalog_provider(request: Request) -> CatalogProvider:
    return EarthSearchProvider(request.app.state.earth_search_client)


def get_catalog_service(
    provider: Annotated[CatalogProvider, Depends(get_catalog_provider)],
) -> CatalogService:
    return CatalogService(provider)


def get_tile_provider(request: Request) -> TileProvider:
    return TiTilerProvider(request.app.state.titiler_client)


def get_tile_service(
    provider: Annotated[TileProvider, Depends(get_tile_provider)],
) -> TileService:
    return TileService(provider)


def get_raster_provider() -> RasterProvider:
    """Dependency provider for RasterProvider — returns a COGRasterProvider."""
    return COGRasterProvider()


def get_analytics_engine() -> AnalyticsEngine:
    """Dependency provider for AnalyticsEngine (stub)."""
    raise NotImplementedError("AnalyticsEngine not yet implemented")


def get_analysis_service(
    provider: Annotated[RasterProvider, Depends(get_raster_provider)],
) -> AnalysisService:
    """Dependency provider for AnalysisService."""
    return AnalysisService(
        raster_provider=provider,
        index_registry=default_index_registry,
        statistics_engine=default_statistics_engine,
    )
