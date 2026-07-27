import datetime
import uuid

import pytest
from pydantic import ValidationError

from src.async_processing.enums import JobStatus
from src.async_processing.models import JobProgress, JobRecord


def test_job_progress_defaults():
    progress = JobProgress()
    assert progress.percentage == 0.0
    assert progress.current_step == 0
    assert progress.total_steps == 0
    assert progress.message is None


def test_job_record_immutability():
    now = datetime.datetime.now(datetime.UTC)
    job = JobRecord(
        job_id=uuid.uuid4(),
        task_name="test_task",
        created_at=now,
        updated_at=now,
    )

    assert job.status == JobStatus.PENDING

    # Attempting to mutate should raise an error due to frozen=True
    with pytest.raises(ValidationError):
        job.status = JobStatus.STARTED


def test_job_record_functional_update():
    now = datetime.datetime.now(datetime.UTC)
    job = JobRecord(
        job_id=uuid.uuid4(),
        task_name="test_task",
        created_at=now,
        updated_at=now,
    )

    # Use model_copy to functionally update
    new_job = job.model_copy(update={"status": JobStatus.SUCCESS})

    assert job.status == JobStatus.PENDING
    assert new_job.status == JobStatus.SUCCESS
