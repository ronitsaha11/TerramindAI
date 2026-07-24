from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from redis.asyncio import Redis

from src.dependencies.database import get_db
from src.dependencies.redis import get_redis
from src.schemas.responses import SuccessResponse

router = APIRouter(tags=["health"])

@router.get("/health", response_model=SuccessResponse[dict])
async def health_check() -> SuccessResponse[dict]:
    """
    Basic health check returning static status.
    """
    return SuccessResponse(data={"status": "healthy"})

@router.get("/ready", response_model=SuccessResponse[dict])
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> SuccessResponse[dict]:
    """
    Readiness check that verifies connections to Postgres and Redis.
    """
    try:
        # Check Database
        await db.execute(text("SELECT 1"))
        
        # Check Redis
        await redis.ping()
        
        return SuccessResponse(data={"status": "ready", "database": "up", "redis": "up"})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}"
        )
