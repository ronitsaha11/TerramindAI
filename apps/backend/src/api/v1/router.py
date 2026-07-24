from fastapi import APIRouter
from src.api.v1.health import router as health_router

api_router = APIRouter()

api_router.include_router(health_router)
# Future routes will be included here:
# api_router.include_router(projects.router, prefix="/projects")
