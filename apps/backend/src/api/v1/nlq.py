import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.dependencies import get_natural_query_service
from src.core.exceptions import AppException
from src.nlq.exceptions import InterpretationError, InterpreterUnavailableError
from src.nlq.models import NaturalQueryRequest, NaturalQueryResult
from src.nlq.service import NaturalQueryService
from src.schemas.responses import SuccessResponse

router = APIRouter(prefix="/projects/{project_id}/query", tags=["natural-language"])


@router.post("/natural", response_model=SuccessResponse[NaturalQueryResult])
async def natural_query(
    project_id: uuid.UUID,
    payload: NaturalQueryRequest,
    service: Annotated[NaturalQueryService, Depends(get_natural_query_service)],
) -> SuccessResponse[NaturalQueryResult]:
    """Answer a plain-language question using the existing spatial engine.

    The reply carries `data.result` as a GeoJSON FeatureCollection in exactly
    the shape the map already renders, alongside the interpretation that
    produced it so a human can check what the question was understood to mean.
    """
    try:
        result = await service.answer(project_id, payload.query)
    except InterpreterUnavailableError as exc:
        raise AppException(status_code=503, detail=str(exc)) from exc
    except InterpretationError as exc:
        raise AppException(
            status_code=422,
            detail=f"That question could not be turned into a spatial query: {exc}",
        ) from exc

    return SuccessResponse(data=result)
