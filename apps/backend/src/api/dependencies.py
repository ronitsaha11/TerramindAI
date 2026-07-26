from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from src.ai.loader import AIModelLoader
from src.ai.manager import ModelManager
from src.ai.models import ModelMetadata
from src.ai.processing.postprocessor import SegmentationPostprocessor
from src.ai.processing.preprocessor import RasterPreprocessor
from src.ai.providers.segformer import SegFormerModel
from src.ai.registry import ModelRegistry
from src.ai.service import AIInferenceService
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


@lru_cache
def get_model_manager() -> ModelManager:
    """Dependency provider for ModelManager (Singleton)."""
    registry = ModelRegistry()

    segformer_meta = ModelMetadata(
        model_id="segformer-b0",
        name="SegFormer B0",
        version="v1",
        description="Semantic segmentation model",
        supported_bands=["RED", "GREEN", "BLUE"],
    )
    registry.register(segformer_meta, SegFormerModel)

    loader = AIModelLoader()
    return ModelManager(registry, loader)


def get_raster_preprocessor() -> RasterPreprocessor:
    """Dependency provider for RasterPreprocessor."""
    return RasterPreprocessor()


def get_segmentation_postprocessor() -> SegmentationPostprocessor:
    """Dependency provider for SegmentationPostprocessor."""
    return SegmentationPostprocessor()


def get_ai_inference_service(
    model_manager: Annotated[ModelManager, Depends(get_model_manager)],
    preprocessor: Annotated[RasterPreprocessor, Depends(get_raster_preprocessor)],
    postprocessor: Annotated[
        SegmentationPostprocessor, Depends(get_segmentation_postprocessor)
    ],
) -> AIInferenceService:
    """Dependency provider for AIInferenceService."""
    return AIInferenceService(
        model_manager=model_manager,
        preprocessor=preprocessor,
        postprocessor=postprocessor,
    )
