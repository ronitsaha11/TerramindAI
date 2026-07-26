from unittest.mock import MagicMock, patch

import pytest
import torch

from src.ai.exceptions import InferenceExecutionError, ModelLoadError
from src.ai.loader import AIModelLoader
from src.ai.manager import ModelManager
from src.ai.models import ModelMetadata
from src.ai.providers.segformer import SegFormerModel
from src.ai.registry import ModelRegistry


@pytest.fixture
def dummy_metadata():
    return ModelMetadata(
        model_id="test-segformer",
        name="Test SegFormer",
        version="v1",
        supported_bands=["RED", "GREEN", "BLUE"],
    )


def test_provider_construction(dummy_metadata):
    provider = SegFormerModel(dummy_metadata, mock_mode=True)
    assert provider.metadata.model_id == "test-segformer"
    assert provider.mock_mode is True


def test_automatic_device_selection(dummy_metadata):
    # In mock mode, the device should be "mock"
    provider = SegFormerModel(dummy_metadata, mock_mode=True)
    assert provider._device == "mock"


def test_load_weights_mock_mode(dummy_metadata):
    provider = SegFormerModel(dummy_metadata, mock_mode=True)
    provider.load_weights()
    assert provider._model == "mock_model_initialized"


def test_deterministic_predictions(dummy_metadata):
    provider = SegFormerModel(dummy_metadata, mock_mode=True)
    provider.load_weights()

    tensor1 = provider.predict(torch.ones(1, 3, 512, 512))
    tensor2 = provider.predict(torch.ones(1, 3, 512, 512))

    # Check shape
    assert tensor1.shape == (1, 150, 512, 512)
    # Check deterministic/repeated predictions
    assert torch.equal(tensor1, tensor2)


def test_model_load_error_wrapping(dummy_metadata):
    import sys

    # Patch sys.modules to mock transformers completely since importing it fails on CI
    # due to Windows blocking regex DLLs
    mock_transformers = MagicMock()
    mock_segformer = mock_transformers.SegformerForSemanticSegmentation
    mock_segformer.from_pretrained.side_effect = Exception("Failed download")
    with patch.dict(sys.modules, {"transformers": mock_transformers}):
        # In non-mock mode, SegFormerModel attempts to import torch.
        provider = SegFormerModel(dummy_metadata, mock_mode=False)
        with pytest.raises(ModelLoadError, match="Failed to load SegFormer model"):
            provider.load_weights()


def test_inference_execution_error_wrapping(dummy_metadata):
    provider = SegFormerModel(dummy_metadata, mock_mode=False)
    # Force _device to CPU for this mock test
    provider._device = torch.device("cpu")

    # Create a mock model that raises an exception during inference
    mock_model = MagicMock()
    mock_model.side_effect = Exception("Forward pass failed")
    provider._model = mock_model

    dummy_input = torch.ones(1, 3, 512, 512)
    with pytest.raises(InferenceExecutionError, match="Inference execution failed"):
        provider.predict(dummy_input)


def test_torch_no_grad_behavior(dummy_metadata):
    provider = SegFormerModel(dummy_metadata, mock_mode=False)
    provider._device = torch.device("cpu")

    mock_model = MagicMock()
    mock_model.return_value.logits = torch.ones(1, 150, 512, 512)
    provider._model = mock_model

    dummy_input = torch.ones(1, 3, 512, 512)

    with patch("torch.no_grad") as mock_no_grad:
        provider.predict(dummy_input)
        mock_no_grad.assert_called_once()


def test_registration_through_registry(dummy_metadata):
    registry = ModelRegistry()
    registry.register(dummy_metadata, SegFormerModel)

    metadata, model_class = registry.lookup("test-segformer")
    assert model_class is SegFormerModel
    assert metadata.model_id == "test-segformer"


def test_loading_through_loader(dummy_metadata):
    registry = ModelRegistry()
    registry.register(dummy_metadata, SegFormerModel)

    loader = AIModelLoader()
    _, provider_class = registry.lookup("test-segformer")

    with patch.object(SegFormerModel, "load"):
        model_instance = loader.initialize_provider(provider_class)

    assert isinstance(model_instance, SegFormerModel)
    # The default instance created by initialize_provider has default metadata,
    # but let's check it doesn't crash.
    assert model_instance.metadata.model_id == "segformer-b0"
    # Wait, the prompt says "loading through AIModelLoader". The loader expects
    # provider_class(). We can just test that it returns the instance.


def test_cache_reuse_through_manager(dummy_metadata):
    registry = ModelRegistry()
    registry.register(dummy_metadata, SegFormerModel)
    loader = AIModelLoader()
    manager = ModelManager(registry, loader)

    with patch.object(SegFormerModel, "load"):
        # Load first time
        model1 = manager.get_model("test-segformer")

        # Load second time
        model2 = manager.get_model("test-segformer")

    # Ensure they are the exact same instance
    assert model1 is model2
