from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.ai.exceptions import (
    InferenceExecutionError,
    InferenceValidationError,
    ModelLoadError,
    PreprocessingError,
)
from src.ai.models import InferenceRequest, InferenceResult
from src.ai.service import AIInferenceService
from src.api.dependencies import get_ai_inference_service

router = APIRouter(prefix="/ai", tags=["AI Inference"])


@router.post(
    "/inference",
    response_model=InferenceResult,
    summary="Execute AI inference",
    description=(
        "Executes a complete AI inference pipeline (preprocessing, model execution, "
        "postprocessing) on the given raster data."
    ),
    responses={
        422: {"description": "Validation or Preprocessing Error"},
        500: {"description": "Inference Execution Error"},
        503: {"description": "Model Loading Error"},
    },
)
async def execute_inference(
    request: InferenceRequest,
    service: Annotated[AIInferenceService, Depends(get_ai_inference_service)],
) -> InferenceResult:
    try:
        result = await service.execute_inference(request)
        return result
    except (InferenceValidationError, PreprocessingError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except ModelLoadError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        ) from e
    except InferenceExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during inference.",
        ) from e
