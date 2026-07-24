from fastapi import APIRouter

from src.api.v1.health import router as health_router
from src.api.v1.projects import router as projects_router
from src.api.v1.regions import router as regions_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(projects_router)
api_router.include_router(regions_router)
