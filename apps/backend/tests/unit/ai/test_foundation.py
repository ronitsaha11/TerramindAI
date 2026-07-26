import uuid

import pytest
from pydantic import ValidationError

from src.ai.base import (
    AbstractAIModel,
    AbstractInferenceProvider,
    AbstractPostprocessor,
    AbstractPreprocessor,
)
from src.ai.exceptions import (
    AIException,
    InferenceExecutionError,
    InferenceValidationError,
    ModelLoadError,
    ModelNotFoundError,
    PostprocessingError,
    PreprocessingError,
)
from src.ai.models import (
    InferenceRequest,
    InferenceResult,
    ModelMetadata,
    PredictionMetadata,
)


def test_exception_inheritance():
    """Verify all specific AI exceptions inherit from AIException."""
    assert issubclass(ModelLoadError, AIException)
    assert issubclass(InferenceExecutionError, AIException)
    assert issubclass(PreprocessingError, AIException)
    assert issubclass(PostprocessingError, AIException)
    assert issubclass(ModelNotFoundError, AIException)
    assert issubclass(InferenceValidationError, AIException)


def test_abstract_class_instantiation_raises_type_error():
    """Verify abstract classes cannot be instantiated."""
    with pytest.raises(TypeError):
        AbstractPreprocessor()  # type: ignore

    with pytest.raises(TypeError):
        AbstractPostprocessor()  # type: ignore

    with pytest.raises(TypeError):
        AbstractAIModel()  # type: ignore

    with pytest.raises(TypeError):
        AbstractInferenceProvider()  # type: ignore


def test_model_metadata_validation():
    """Verify ModelMetadata Pydantic validation."""
    metadata = ModelMetadata(
        model_id="test-model",
        name="Test Model",
        version="1.0.0",
        supported_bands=["RED", "NIR"],
        hyperparameters={"threshold": 0.5},
    )
    assert metadata.model_id == "test-model"
    assert metadata.supported_bands == ["RED", "NIR"]

    # Missing required field
    with pytest.raises(ValidationError):
        ModelMetadata(
            model_id="test-model",
            name="Test Model",
            version="1.0.0",
            supported_bands=["RED"],
            # missing required field
        )


def test_inference_request_validation():
    """Verify InferenceRequest Pydantic validation."""
    project_id = uuid.uuid4()
    request = InferenceRequest(
        project_id=project_id,
        scene_id="s3://test/scene.tif",
        model_id="test-model",
        parameters={"foo": "bar"},
    )
    assert request.project_id == project_id
    assert request.parameters == {"foo": "bar"}

    # Invalid project_id type (not a UUID)
    with pytest.raises(ValidationError):
        InferenceRequest(
            project_id="not-a-uuid",  # type: ignore
            scene_id="s3://test/scene.tif",
            model_id="test-model",
        )


def test_inference_result_serialization():
    """Verify InferenceResult serialization."""
    request_id = uuid.uuid4()
    metadata = PredictionMetadata(
        confidence_score=0.95, execution_time_ms=125.5, model_version="1.0.0"
    )
    result = InferenceResult(
        request_id=request_id,
        prediction_metadata=metadata,
        result_data={"feature_count": 42},
    )

    serialized = result.model_dump()
    assert serialized["request_id"] == request_id
    assert serialized["prediction_metadata"]["confidence_score"] == 0.95
    assert serialized["result_data"]["feature_count"] == 42


def test_prediction_metadata_type_validation():
    """Verify PredictionMetadata field validations."""
    # confidence_score > 1.0 should fail
    with pytest.raises(ValidationError):
        PredictionMetadata(
            confidence_score=1.5, execution_time_ms=100.0, model_version="1.0"
        )

    # confidence_score < 0.0 should fail
    with pytest.raises(ValidationError):
        PredictionMetadata(
            confidence_score=-0.1, execution_time_ms=100.0, model_version="1.0"
        )
