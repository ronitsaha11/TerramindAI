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
from src.api.dependencies import get_ai_inference_service, get_geospatial_service
from src.geospatial.exceptions import GeospatialExecutionError
from src.geospatial.models import PolygonizationRequest
from src.geospatial.service import GeospatialService

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
    geospatial_service: Annotated[GeospatialService, Depends(get_geospatial_service)],
) -> InferenceResult:
    try:
        result = await service.execute_inference(request)

        # Check if geospatial vectorization was requested
        if request.parameters.get("export_geojson"):
            mask = result.result_data.get("mask")
            transform = request.parameters.get("transform")
            crs = request.parameters.get("crs")

            if mask is not None and transform and crs:
                import numpy as np
                from affine import Affine

                # Check if mask is already a numpy array, if not convert it
                if not isinstance(mask, np.ndarray):
                    mask = np.array(mask, dtype=np.uint8)

                if not isinstance(transform, Affine):
                    transform = Affine(*transform)

                poly_request = PolygonizationRequest(
                    mask=mask, transform=transform, crs=crs
                )
                export_result = geospatial_service.process_mask(poly_request)

                # We need to construct a new InferenceResult since they are frozen
                result = InferenceResult(
                    request_id=result.request_id,
                    prediction_metadata=result.prediction_metadata,
                    result_data=result.result_data,
                    geojson=export_result.feature_collection,
                )

        return result
    except (InferenceValidationError, PreprocessingError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except ModelLoadError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        ) from e
    except (InferenceExecutionError, GeospatialExecutionError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during inference.",
        ) from e
