from fastapi import APIRouter

from src.api.v1.ai import router as ai_router
from src.api.v1.analysis import router as analysis_router
from src.api.v1.datasets import router as datasets_router
from src.api.v1.geospatial import router as geospatial_router
from src.api.v1.health import router as health_router
from src.api.v1.jobs import router as jobs_router
from src.api.v1.nlq import router as nlq_router
from src.api.v1.projects import router as projects_router
from src.api.v1.regions import router as regions_router
from src.api.v1.scenes import router as scenes_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(projects_router)
api_router.include_router(datasets_router)
api_router.include_router(nlq_router)
api_router.include_router(regions_router)
api_router.include_router(scenes_router)
api_router.include_router(analysis_router)
api_router.include_router(ai_router)
api_router.include_router(geospatial_router)
api_router.include_router(jobs_router)
