from typing import Annotated

import numpy as np
from affine import Affine
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from src.api.dependencies import get_geospatial_service
from src.geospatial.exceptions import GeospatialExecutionError
from src.geospatial.models import GeoJSONExportResult, PolygonizationRequest
from src.geospatial.service import GeospatialService

router = APIRouter(prefix="/geospatial", tags=["Geospatial Processing Engine"])


class VectorizeRequest(BaseModel):
    """Payload for raster to vector conversion."""

    model_config = ConfigDict(frozen=True)

    mask: list[list[int]] = Field(
        ..., description="2D segmentation mask as a list of lists"
    )
    transform: tuple[float, float, float, float, float, float] = Field(
        ..., description="6-element affine transform"
    )
    crs: str = Field(..., description="Coordinate Reference System (e.g., EPSG:4326)")


@router.post(
    "/vectorize",
    response_model=GeoJSONExportResult,
    summary="Vectorize Raster Mask",
    description=(
        "Vectorize a raw segmentation mask into an RFC 7946 GeoJSON FeatureCollection."
    ),
    responses={
        422: {"description": "Validation Error"},
        500: {"description": "Geospatial Execution Error"},
    },
)
async def vectorize_mask(
    request: VectorizeRequest,
    service: Annotated[GeospatialService, Depends(get_geospatial_service)],
) -> GeoJSONExportResult:
    """Execute the geospatial processing pipeline."""
    try:
        # Convert the incoming list of lists into a NumPy array
        mask_array = np.array(request.mask, dtype=np.uint8)

        # Convert the 6-element tuple to an Affine object
        transform_obj = Affine(*request.transform)

        polygonization_request = PolygonizationRequest(
            mask=mask_array,
            transform=transform_obj,
            crs=request.crs,
        )

        result = service.process_mask(polygonization_request)
        return result

    except GeospatialExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
    except ValueError as e:
        # Catch NumPy parsing errors or affine errors as 422
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid payload format: {str(e)}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during vectorization.",
        ) from e
