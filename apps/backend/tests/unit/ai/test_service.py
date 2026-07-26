import uuid
from unittest.mock import MagicMock

import pytest

from src.ai.exceptions import (
    InferenceExecutionError,
    InferenceValidationError,
    ModelLoadError,
    PostprocessingError,
    PreprocessingError,
)
from src.ai.models import InferenceRequest, InferenceResult
from src.ai.service import AIInferenceService


@pytest.fixture
def mock_preprocessor():
    preprocessor = MagicMock()
    preprocessor.preprocess.return_value = "mock_tensor"
    return preprocessor


@pytest.fixture
def mock_postprocessor():
    postprocessor = MagicMock()
    postprocessor.postprocess.return_value = {"mask": "mock_mask"}
    return postprocessor


@pytest.fixture
def mock_model():
    model = MagicMock()
    model.predict.return_value = "mock_logits"
    model.metadata.version = "1.0.0"
    return model


@pytest.fixture
def mock_model_manager(mock_model):
    manager = MagicMock()
    manager.get_model.return_value = mock_model
    return manager


@pytest.fixture
def dummy_request():
    return InferenceRequest(
        project_id=uuid.uuid4(),
        scene_id="test_scene",
        model_id="test_model",
        parameters={"raw_data": "mock_raw_data"},
    )


@pytest.mark.asyncio
async def test_successful_orchestration(
    mock_model_manager, mock_preprocessor, mock_postprocessor, mock_model, dummy_request
):
    service = AIInferenceService(
        model_manager=mock_model_manager,
        preprocessor=mock_preprocessor,
        postprocessor=mock_postprocessor,
    )

    result = await service.execute_inference(dummy_request)

    # Verify dependency injection & invocations
    mock_preprocessor.preprocess.assert_called_once_with(dummy_request, "mock_raw_data")
    mock_model_manager.get_model.assert_called_once_with("test_model")
    mock_model.predict.assert_called_once_with(
        preprocessed_data="mock_tensor", parameters=dummy_request.parameters
    )
    mock_postprocessor.postprocess.assert_called_once_with(dummy_request, "mock_logits")

    # Verify InferenceResult generation
    assert isinstance(result, InferenceResult)
    assert result.result_data["mask"] == "mock_mask"
    assert result.result_data["model_id"] == "test_model"
    assert "timestamp" in result.result_data
    assert result.prediction_metadata.model_version == "1.0.0"
    assert result.prediction_metadata.execution_time_ms >= 0


@pytest.mark.asyncio
async def test_repeated_inference(
    mock_model_manager, mock_preprocessor, mock_postprocessor, mock_model, dummy_request
):
    service = AIInferenceService(
        model_manager=mock_model_manager,
        preprocessor=mock_preprocessor,
        postprocessor=mock_postprocessor,
    )

    await service.execute_inference(dummy_request)
    await service.execute_inference(dummy_request)

    # Every dependency should have been invoked exactly twice (once per inference)
    assert mock_preprocessor.preprocess.call_count == 2
    assert mock_model_manager.get_model.call_count == 2
    assert mock_model.predict.call_count == 2
    assert mock_postprocessor.postprocess.call_count == 2


@pytest.mark.asyncio
async def test_missing_raw_data():
    service = AIInferenceService(
        model_manager=MagicMock(),
        preprocessor=MagicMock(),
        postprocessor=MagicMock(),
    )

    invalid_request = InferenceRequest(
        project_id=uuid.uuid4(),
        scene_id="test_scene",
        model_id="test_model",
        parameters={},
    )

    with pytest.raises(InferenceValidationError, match="Missing 'raw_data'"):
        await service.execute_inference(invalid_request)


@pytest.mark.asyncio
async def test_exception_propagation(
    mock_model_manager, mock_preprocessor, mock_postprocessor, mock_model, dummy_request
):
    service = AIInferenceService(
        model_manager=mock_model_manager,
        preprocessor=mock_preprocessor,
        postprocessor=mock_postprocessor,
    )

    # 1. PreprocessingError
    mock_preprocessor.preprocess.side_effect = PreprocessingError("Preprocess failed")
    with pytest.raises(PreprocessingError, match="Preprocess failed"):
        await service.execute_inference(dummy_request)
    mock_preprocessor.preprocess.side_effect = None  # Reset

    # 2. ModelLoadError
    mock_model_manager.get_model.side_effect = ModelLoadError("Load failed")
    with pytest.raises(ModelLoadError, match="Load failed"):
        await service.execute_inference(dummy_request)
    mock_model_manager.get_model.side_effect = None

    # 3. PostprocessingError
    mock_postprocessor.postprocess.side_effect = PostprocessingError("Post failed")
    with pytest.raises(PostprocessingError, match="Post failed"):
        await service.execute_inference(dummy_request)
    mock_postprocessor.postprocess.side_effect = None

    # 4. Unknown Exception translation
    mock_model.predict.side_effect = ValueError("Some weird numpy error")
    with pytest.raises(
        InferenceExecutionError, match="Unexpected error during inference orchestration"
    ):
        await service.execute_inference(dummy_request)
