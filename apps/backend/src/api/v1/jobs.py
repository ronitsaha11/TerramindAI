import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.dependencies import get_job_service
from src.async_processing.enums import JobStatus
from src.async_processing.exceptions import (
    InvalidJobOperationError,
    JobCancellationError,
    JobRetryError,
)
from src.async_processing.models import JobProgress, JobRecord
from src.async_processing.service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobIdResponse(BaseModel):
    """Response model containing a job ID."""

    job_id: uuid.UUID
    status: JobStatus
    message: str


@router.post(
    "/ai/inference",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobIdResponse,
)
async def submit_ai_inference(
    payload: dict[str, Any],
    job_service: Annotated[JobService, Depends(get_job_service)],
) -> JobIdResponse:
    """Submit an asynchronous AI inference job."""
    job_id = job_service.submit_ai_inference(payload)
    return JobIdResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="AI inference job accepted.",
    )


@router.post(
    "/geospatial/vectorize",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobIdResponse,
)
async def submit_geospatial_vectorization(
    payload: dict[str, Any],
    job_service: Annotated[JobService, Depends(get_job_service)],
) -> JobIdResponse:
    """Submit an asynchronous Geospatial vectorization job."""
    job_id = job_service.submit_geospatial_vectorization(payload)
    return JobIdResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Geospatial vectorization job accepted.",
    )


@router.get(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=JobRecord,
)
async def get_job(
    job_id: uuid.UUID,
    job_service: Annotated[JobService, Depends(get_job_service)],
) -> JobRecord:
    """Retrieve the complete job record."""
    return job_service.get_job(job_id)


@router.get(
    "/{job_id}/status",
    status_code=status.HTTP_200_OK,
)
async def get_job_status(
    job_id: uuid.UUID,
    job_service: Annotated[JobService, Depends(get_job_service)],
) -> dict[str, Any]:
    """Retrieve only the job status."""
    status_enum = job_service.get_job_status(job_id)
    return {"job_id": job_id, "status": status_enum}


@router.get(
    "/{job_id}/progress",
    status_code=status.HTTP_200_OK,
    response_model=JobProgress | None,
)
async def get_job_progress(
    job_id: uuid.UUID,
    job_service: Annotated[JobService, Depends(get_job_service)],
) -> JobProgress | None:
    """Retrieve the job progress."""
    return job_service.get_job_progress(job_id)


@router.get(
    "/{job_id}/result",
    status_code=status.HTTP_200_OK,
)
async def get_job_result(
    job_id: uuid.UUID,
    job_service: Annotated[JobService, Depends(get_job_service)],
) -> dict[str, Any]:
    """Retrieve the job result reference."""
    # InvalidJobOperationError will be mapped to 400 Bad Request by global handler
    # but we can explicitly raise 409 Conflict if not completed, per REST semantics.
    try:
        result_ref = job_service.get_job_result(job_id)
        return {"job_id": job_id, "result_reference": result_ref}
    except InvalidJobOperationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_job(
    job_id: uuid.UUID,
    job_service: Annotated[JobService, Depends(get_job_service)],
) -> None:
    """Cancel a running or pending job."""
    try:
        job_service.cancel_job(job_id)
    except JobCancellationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post(
    "/{job_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobIdResponse,
)
async def retry_job(
    job_id: uuid.UUID,
    job_service: Annotated[JobService, Depends(get_job_service)],
) -> JobIdResponse:
    """Retry an eligible failed job."""
    try:
        job_service.retry_job(job_id)
        return JobIdResponse(
            job_id=job_id,
            status=JobStatus.RETRY,
            message="Job retry accepted.",
        )
    except JobRetryError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[JobRecord],
)
async def list_jobs(
    job_service: Annotated[JobService, Depends(get_job_service)],
) -> list[JobRecord]:
    """Retrieve all known jobs."""
    return job_service.list_jobs()
