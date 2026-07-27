from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.async_processing.enums import JobStatus


class JobProgress(BaseModel):
    """Tracks the progress of an asynchronous job."""

    percentage: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Completion percentage"
    )
    current_step: int = Field(default=0, ge=0, description="Current step index")
    total_steps: int = Field(default=0, ge=0, description="Total number of steps")
    message: str | None = Field(
        default=None, description="Human-readable progress message"
    )


class JobRecord(BaseModel):
    """
    Immutable record representing the state of an asynchronous job.
    """

    model_config = ConfigDict(frozen=True)

    job_id: UUID = Field(..., description="Unique identifier for the job")
    task_name: str = Field(..., description="Registered name of the task to execute")
    status: JobStatus = Field(
        default=JobStatus.PENDING, description="Current lifecycle state"
    )
    created_at: datetime = Field(..., description="Timestamp when the job was created")
    updated_at: datetime = Field(..., description="Timestamp of the last status update")
    progress: JobProgress | None = Field(
        default=None, description="Optional progress tracking"
    )
    result_reference: str | None = Field(
        default=None, description="Reference to the persisted result"
    )
    error_message: str | None = Field(
        default=None, description="Error message if the job failed"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary task metadata"
    )
