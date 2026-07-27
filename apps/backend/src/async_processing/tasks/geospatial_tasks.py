import uuid
from typing import Any

from celery import Task
from celery.exceptions import Retry

from src.api.dependencies import (
    get_geojson_exporter,
    get_geometry_processor,
    get_geospatial_service,
    get_polygonizer,
    get_spatial_analytics_engine,
)
from src.async_processing.celery_app import app
from src.async_processing.exceptions import TaskExecutionError
from src.async_processing.manager import get_task_manager
from src.async_processing.models import JobProgress
from src.async_processing.registry import default_registry
from src.geospatial.exceptions import (
    GeospatialExecutionError,
)
from src.geospatial.models import PolygonizationRequest
from src.geospatial.service import GeospatialService

TRANSIENT_EXCEPTIONS = (ConnectionError, TimeoutError, IOError)


def _build_geospatial_service() -> GeospatialService:
    """Instantiate GeospatialService using the existing DI components."""
    polygonizer = get_polygonizer()
    geometry_processor = get_geometry_processor()
    analytics_engine = get_spatial_analytics_engine()
    geojson_exporter = get_geojson_exporter()
    return get_geospatial_service(
        polygonizer=polygonizer,
        geometry_processor=geometry_processor,
        analytics_engine=analytics_engine,
        geojson_exporter=geojson_exporter,
    )


@app.task(bind=True, max_retries=3, retry_backoff=True, retry_jitter=True)
def run_geospatial_vectorization_task(
    self: Task, job_id_str: str, request_data: dict[str, Any]
) -> None:
    """
    Celery task that orchestrates the execution of the Geospatial processing pipeline.
    Acts purely as an orchestration wrapper.
    """
    job_id = uuid.UUID(job_id_str)
    manager = get_task_manager()

    try:
        manager.acknowledge_receipt(job_id)
        manager.start_job(job_id)

        # 10% Preparing raster mask
        manager.update_progress(
            job_id,
            JobProgress(
                percentage=10.0,
                current_step=1,
                total_steps=6,
                message="Preparing raster mask",
            ),
        )

        request = PolygonizationRequest(**request_data)
        geo_service = _build_geospatial_service()

        # Execute the pipeline (synchronous blocking call)
        # Intermediate steps cannot be emitted internally without duplication.
        _ = geo_service.process_mask(request)

        # 95% GeoJSON serialization
        manager.update_progress(
            job_id,
            JobProgress(
                percentage=95.0,
                current_step=5,
                total_steps=6,
                message="GeoJSON serialization",
            ),
        )

        # Store result reference (simulated local path for foundation phase)
        result_reference = f"local://results/geojson/{job_id}.json"

        # 100% Completed
        manager.mark_success(job_id, result_reference=result_reference)

    except GeospatialExecutionError as e:
        # Check the underlying cause to distinguish transient vs domain errors
        cause = e.__cause__
        if cause is not None and isinstance(cause, TRANSIENT_EXCEPTIONS):
            manager.mark_retry(job_id)
            raise self.retry(exc=e) from e

        # If it's a domain error or something else non-transient
        manager.mark_failure(job_id, error_message=str(e))
        raise TaskExecutionError(str(e)) from e

    except TRANSIENT_EXCEPTIONS as e:
        # Caught transient error directly
        manager.mark_retry(job_id)
        raise self.retry(exc=e) from e

    except Retry:
        raise

    except Exception as e:
        # Unexpected framework/infrastructure errors
        manager.mark_failure(job_id, error_message=str(e))
        raise TaskExecutionError(f"Unexpected error: {str(e)}") from e


default_registry.register(
    "run_geospatial_vectorization_task", run_geospatial_vectorization_task
)
