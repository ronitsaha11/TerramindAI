from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ModelMetadata(BaseModel):
    """Metadata describing an AI model."""

    model_config = ConfigDict(frozen=True)

    model_id: str = Field(..., description="Unique identifier for the model")
    name: str = Field(..., description="Human-readable name of the model")
    version: str = Field(..., description="Version string of the model")
    description: str | None = Field(
        default=None, description="Optional description of the model"
    )
    supported_bands: list[str] = Field(
        ...,
        description=(
            "List of band names this model expects (e.g., ['RED', 'GREEN', 'BLUE'])"
        ),
    )
    hyperparameters: dict[str, Any] = Field(
        default_factory=dict, description="Model-specific hyperparameters"
    )


class InferenceRequest(BaseModel):
    """Request payload for executing AI inference."""

    model_config = ConfigDict(frozen=True)

    project_id: UUID = Field(..., description="Project ID associated with this request")
    scene_id: str = Field(
        ..., description="URI or identifier of the source raster scene"
    )
    model_id: str = Field(..., description="Identifier of the AI model to execute")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Dynamic parameters for preprocessing, inference, or postprocessing"
        ),
    )


class PredictionMetadata(BaseModel):
    """Metadata summarizing an inference execution."""

    model_config = ConfigDict(frozen=True)

    confidence_score: float | None = Field(
        default=None,
        description="Aggregate confidence score if applicable",
        ge=0.0,
        le=1.0,
    )
    execution_time_ms: float = Field(
        ..., description="Time taken to execute inference in milliseconds"
    )
    model_version: str = Field(
        ..., description="Version of the model used for inference"
    )


class InferenceResult(BaseModel):
    """Result of an AI inference execution."""

    model_config = ConfigDict(frozen=True)

    request_id: UUID = Field(
        ..., description="Identifier mapping back to the initial request"
    )
    prediction_metadata: PredictionMetadata = Field(
        ..., description="Metadata regarding the prediction execution"
    )
    # In a real implementation, the result might contain vector features,
    # mask URIs, or aggregate stats.
    # We leave this as a flexible dictionary for the foundation.
    result_data: dict[str, Any] = Field(
        default_factory=dict,
        description="The actual output data from the postprocessor",
    )
    geojson: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional GeoJSON FeatureCollection generated from the segmentation mask"
        ),
    )
