import logging
from typing import Any

import torch

from src.ai.base import AbstractPostprocessor
from src.ai.exceptions import PostprocessingError
from src.ai.models import InferenceRequest

logger = logging.getLogger(__name__)


class SegmentationPostprocessor(AbstractPostprocessor):
    """
    Converts raw segmentation model logits into NumPy mask arrays.
    """

    def postprocess(
        self, request: InferenceRequest, model_output: Any
    ) -> dict[str, Any]:
        """
        Postprocess model logits into a semantic segmentation mask.

        Args:
            request: InferenceRequest containing parameters.
            model_output: Raw model logits (PyTorch tensor).

        Returns:
            Dictionary containing the segmentation mask as a NumPy array (H, W).

        Raises:
            PostprocessingError: If postprocessing fails or input is invalid.
        """
        try:
            if not isinstance(model_output, torch.Tensor):
                out_type = type(model_output).__name__
                raise PostprocessingError(
                    f"Expected model_output to be a PyTorch tensor, got {out_type}"
                )

            # move tensors to CPU and detach gradients
            tensor = model_output.cpu().detach()

            # validate tensor dimensions
            if tensor.ndim != 4:
                raise PostprocessingError(
                    f"Expected logits tensor to have 4 dimensions (B, C, H, W), "
                    f"got {tensor.ndim}"
                )

            # compute argmax over class dimension (dim 1)
            # Logits shape: (B, C, H, W) -> argmax shape: (B, H, W)
            mask_tensor = torch.argmax(tensor, dim=1)

            # We assume a batch size of 1 for a single inference request.
            # Remove the batch dimension -> shape: (Height, Width)
            mask_tensor = mask_tensor.squeeze(0)

            # validate output shape (H, W)
            if mask_tensor.ndim != 2:
                raise PostprocessingError(
                    f"Expected output mask to have 2 dimensions (H, W), "
                    f"got {mask_tensor.ndim}"
                )

            # convert to NumPy array
            mask_array = mask_tensor.numpy()

            return {"mask": mask_array}

        except PostprocessingError:
            raise
        except Exception as e:
            logger.error(f"Failed to postprocess model output: {e}")
            raise PostprocessingError(f"Postprocessing failed: {e}") from e
