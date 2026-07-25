from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.analytics.exceptions import (
    AnalysisValidationError,
    ProviderError,
    RasterOpenError,
    StatisticsError,
)
from src.analytics.models import AnalysisRequest, AnalysisResult
from src.api.dependencies import get_analysis_service
from src.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post(
    "",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Run Earth Intelligence Analysis",
    description=(
        "Executes a complete Earth Intelligence pipeline run. "
        "Coordinates raster reading, spectral index computation, and "
        "statistics generation. Returns a detailed AnalysisResult including "
        "the computed histogram and percentiles."
    ),
    responses={
        400: {
            "description": "Bad Request (e.g., missing required bands, invalid band indices)"
        },
        404: {"description": "Raster or scene not found"},
        422: {
            "description": "Unprocessable Entity (e.g., invalid analysis type, validation error)"
        },
        500: {"description": "Internal Server Error"},
        502: {"description": "External Provider Error"},
    },
)
async def analyze_scene(
    request: AnalysisRequest,
    analysis_service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> AnalysisResult:
    try:
        result = await analysis_service.analyze(request)
        return result
    except RasterOpenError as e:
        # If we can't open it, treat it as a 404 (scene not found) for now.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except AnalysisValidationError as e:
        # Distinguish between 400 (bad parameters) and 422 (unsupported types)
        # Using 400 as a generic catch-all for validation here, although 422 is also fine.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except StatisticsError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
    except ProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
