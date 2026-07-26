import uuid
from unittest.mock import patch

import numpy as np
import pytest
import torch

from src.ai.exceptions import PostprocessingError, PreprocessingError
from src.ai.models import InferenceRequest
from src.ai.processing.postprocessor import SegmentationPostprocessor
from src.ai.processing.preprocessor import RasterPreprocessor


@pytest.fixture
def dummy_request():
    return InferenceRequest(
        project_id=uuid.uuid4(),
        scene_id="test_scene",
        model_id="test_model",
        parameters={},
    )


def test_preprocessor_normalization(dummy_request):
    preprocessor = RasterPreprocessor()

    # uint8
    raw_data_uint8 = np.ones((3, 64, 64), dtype=np.uint8) * 255
    tensor_uint8 = preprocessor.preprocess(dummy_request, raw_data_uint8)
    assert tensor_uint8.max().item() == 1.0

    # uint16
    raw_data_uint16 = np.ones((3, 64, 64), dtype=np.uint16) * 65535
    tensor_uint16 = preprocessor.preprocess(dummy_request, raw_data_uint16)
    assert tensor_uint16.max().item() == 1.0

    # float32 min-max scaling
    raw_data_float = np.random.uniform(10.0, 20.0, (3, 64, 64)).astype(np.float32)
    tensor_float = preprocessor.preprocess(dummy_request, raw_data_float)
    assert pytest.approx(tensor_float.min().item()) == 0.0
    assert pytest.approx(tensor_float.max().item()) == 1.0

    # all zeros float32
    raw_data_zeros = np.zeros((3, 64, 64), dtype=np.float32)
    tensor_zeros = preprocessor.preprocess(dummy_request, raw_data_zeros)
    assert pytest.approx(tensor_zeros.max().item()) == 0.0


def test_preprocessor_tensor_conversion_and_batch_dim(dummy_request):
    preprocessor = RasterPreprocessor()
    raw_data = np.zeros((3, 64, 64), dtype=np.uint8)

    tensor = preprocessor.preprocess(dummy_request, raw_data)

    assert isinstance(tensor, torch.Tensor)
    # Check batch dimension was added
    assert tensor.shape == (1, 3, 64, 64)


def test_preprocessor_dtype_conversion(dummy_request):
    preprocessor = RasterPreprocessor()
    raw_data = np.zeros((3, 64, 64), dtype=np.uint8)

    tensor = preprocessor.preprocess(dummy_request, raw_data)
    assert tensor.dtype == torch.float32


def test_preprocessor_invalid_inputs(dummy_request):
    preprocessor = RasterPreprocessor()

    # Not a numpy array
    with pytest.raises(PreprocessingError, match="Input must be a NumPy array"):
        preprocessor.preprocess(dummy_request, [1, 2, 3])  # type: ignore

    # Invalid dimensions (e.g., 2D instead of 3D)
    with pytest.raises(PreprocessingError, match="Expected array with 3 dimensions"):
        preprocessor.preprocess(dummy_request, np.zeros((64, 64)))


def test_preprocessor_exception_wrapping(dummy_request):
    preprocessor = RasterPreprocessor()
    raw_data = np.zeros((3, 64, 64), dtype=np.uint8)

    with patch("torch.from_numpy", side_effect=Exception("Unexpected tensor error")):
        with pytest.raises(PreprocessingError, match="Preprocessing failed"):
            preprocessor.preprocess(dummy_request, raw_data)


def test_postprocessor_argmax_decoding_and_mask_generation(dummy_request):
    postprocessor = SegmentationPostprocessor()

    # Create mock logits with shape (Batch=1, Classes=3, Height=64, Width=64)
    # Class 1 will be the maximum for all pixels
    logits = torch.zeros((1, 3, 64, 64), dtype=torch.float32)
    logits[0, 1, :, :] = 10.0

    result = postprocessor.postprocess(dummy_request, logits)

    assert "mask" in result
    mask = result["mask"]

    assert isinstance(mask, np.ndarray)
    assert mask.shape == (64, 64)
    # Since Class 1 was 10.0, the argmax should be 1 everywhere
    assert np.all(mask == 1)


def test_postprocessor_invalid_inputs(dummy_request):
    postprocessor = SegmentationPostprocessor()

    # Not a tensor
    with pytest.raises(
        PostprocessingError, match="Expected model_output to be a PyTorch tensor"
    ):
        postprocessor.postprocess(dummy_request, np.zeros((1, 3, 64, 64)))

    # Invalid shape (e.g., missing batch dim)
    with pytest.raises(
        PostprocessingError, match="Expected logits tensor to have 4 dimensions"
    ):
        postprocessor.postprocess(dummy_request, torch.zeros((3, 64, 64)))


def test_postprocessor_exception_wrapping(dummy_request):
    postprocessor = SegmentationPostprocessor()
    logits = torch.zeros((1, 3, 64, 64), dtype=torch.float32)

    with patch("torch.argmax", side_effect=Exception("Unexpected error")):
        with pytest.raises(PostprocessingError, match="Postprocessing failed"):
            postprocessor.postprocess(dummy_request, logits)
