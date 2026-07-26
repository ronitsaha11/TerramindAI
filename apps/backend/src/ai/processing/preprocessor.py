import logging
from typing import Any

import numpy as np
import torch

from src.ai.base import AbstractPreprocessor
from src.ai.exceptions import PreprocessingError
from src.ai.models import InferenceRequest

logger = logging.getLogger(__name__)


class RasterPreprocessor(AbstractPreprocessor):
    """
    Preprocesses raw raster data into PyTorch tensors for AI inference.
    """

    def preprocess(self, request: InferenceRequest, raw_data: Any) -> torch.Tensor:
        """
        Preprocess raw NumPy arrays.

        Args:
            request: InferenceRequest containing parameters.
            raw_data: NumPy array of shape (C, H, W).

        Returns:
            PyTorch tensor of shape (1, C, H, W) normalized to [0, 1].

        Raises:
            PreprocessingError: If input shape/dtype is invalid or preprocessing fails.
        """
        try:
            if not isinstance(raw_data, np.ndarray):
                raise PreprocessingError(
                    f"Input must be a NumPy array, got {type(raw_data).__name__}"
                )

            if raw_data.ndim != 3:
                raise PreprocessingError(
                    f"Expected array with 3 dimensions (C, H, W), got {raw_data.ndim}"
                )

            # normalize pixel values to float32
            tensor_data = raw_data.astype(np.float32)

            # scale to [0,1]
            if raw_data.dtype == np.uint8:
                tensor_data = tensor_data / 255.0
            elif raw_data.dtype == np.uint16:
                tensor_data = tensor_data / 65535.0
            else:
                t_min = tensor_data.min()
                t_max = tensor_data.max()
                if t_max > t_min:
                    tensor_data = (tensor_data - t_min) / (t_max - t_min)
                else:
                    # Avoid division by zero
                    tensor_data = np.zeros_like(tensor_data)

            # convert to PyTorch tensor
            tensor = torch.from_numpy(tensor_data)

            # add batch dimension
            tensor = tensor.unsqueeze(0)

            return tensor

        except PreprocessingError:
            raise
        except Exception as e:
            logger.error(f"Failed to preprocess raster data: {e}")
            raise PreprocessingError(f"Preprocessing failed: {e}") from e
