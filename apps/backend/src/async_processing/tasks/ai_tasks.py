import asyncio
import uuid
from typing import Any

from celery import Task
from celery.exceptions import Retry

from src.ai.exceptions import AIException, ModelLoadError
from src.ai.models import InferenceRequest
from src.ai.service import AIInferenceService
from src.api.dependencies import (
    get_ai_inference_service,
    get_model_manager,
    get_raster_preprocessor,
    get_segmentation_postprocessor,
)
from src.async_processing.celery_app import app
from src.async_processing.exceptions import TaskExecutionError
from src.async_processing.manager import get_task_manager
from src.async_processing.models import JobProgress
from src.async_processing.registry import default_registry

TRANSIENT_EXCEPTIONS = (ModelLoadError, ConnectionError, TimeoutError)


def _build_ai_service() -> AIInferenceService:
    """Instantiate AIInferenceService using the existing DI components."""
    model_manager = get_model_manager()
    preprocessor = get_raster_preprocessor()
    postprocessor = get_segmentation_postprocessor()
    return get_ai_inference_service(model_manager, preprocessor, postprocessor)


@app.task(bind=True, max_retries=3, retry_backoff=True, retry_jitter=True)
def run_ai_inference_task(
    self: Task, job_id_str: str, request_data: dict[str, Any]
) -> None:
    """
    Celery task that orchestrates the execution of the AI inference pipeline.
    Acts purely as an orchestration wrapper.
    """
    job_id = uuid.UUID(job_id_str)
    manager = get_task_manager()

    try:
        manager.acknowledge_receipt(job_id)
        manager.start_job(job_id)

        # 10% Initializing inference
        manager.update_progress(
            job_id,
            JobProgress(
                percentage=10.0,
                current_step=1,
                total_steps=6,
                message="Initializing inference",
            ),
        )

        request = InferenceRequest(**request_data)
        ai_service = _build_ai_service()

        # Because execute_inference is a single async call, intermediate
        # progress steps (30%, 60%, 85%) cannot be emitted during its execution
        # without duplicating or injecting logic. We execute the block directly.
        result = asyncio.run(ai_service.execute_inference(request))

        # 95% Serializing output
        manager.update_progress(
            job_id,
            JobProgress(
                percentage=95.0,
                current_step=5,
                total_steps=6,
                message="Serializing output",
            ),
        )

        # Store result reference (simulated local path for foundation phase)
        result_reference = f"local://results/{result.request_id}.json"

        # 100% Completed
        manager.mark_success(job_id, result_reference=result_reference)

    except TRANSIENT_EXCEPTIONS as e:
        manager.mark_retry(job_id)
        raise self.retry(exc=e) from e
    except AIException as e:
        # Domain errors (validation, preprocessing, etc.) are non-transient
        manager.mark_failure(job_id, error_message=str(e))
        raise TaskExecutionError(str(e)) from e
    except Retry:
        raise
    except Exception as e:
        # Unexpected framework/infrastructure errors
        manager.mark_failure(job_id, error_message=str(e))
        raise TaskExecutionError(f"Unexpected error: {str(e)}") from e


default_registry.register("run_ai_inference_task", run_ai_inference_task)
