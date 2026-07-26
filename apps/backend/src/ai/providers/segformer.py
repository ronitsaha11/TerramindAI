import logging
from typing import Any

from src.ai.base import AbstractAIModel
from src.ai.exceptions import InferenceExecutionError, ModelLoadError
from src.ai.models import ModelMetadata

logger = logging.getLogger(__name__)


class SegFormerModel(AbstractAIModel):
    """
    SegFormer AI provider using HuggingFace Transformers and PyTorch.
    """

    def __init__(self, metadata: ModelMetadata | None = None, mock_mode: bool = False):
        """
        Initialize the SegFormer provider.

        Args:
            metadata: The metadata defining this model instance.
            mock_mode: If True, operates without PyTorch/Transformers dependencies
                or weights, for deterministic testing.
        """
        if metadata is None:
            metadata = ModelMetadata(
                model_id="segformer-b0",
                name="SegFormer B0",
                version="1.0",
                supported_bands=["RED", "GREEN", "BLUE"],
            )
        self._metadata = metadata
        self.mock_mode = mock_mode
        self._model: Any = None
        self._device: Any = None

        if not self.mock_mode:
            import torch

            if torch.cuda.is_available():
                self._device = torch.device("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self._device = torch.device("mps")
            else:
                self._device = torch.device("cpu")
            logger.info(f"Initialized SegFormerModel with device: {self._device}")
        else:
            self._device = "mock"
            logger.info("Initialized SegFormerModel in mock mode")

    @property
    def metadata(self) -> ModelMetadata:
        """Get the model metadata."""
        return self._metadata

    def load(self) -> None:
        """
        Load the model into memory/VRAM.
        Required by AbstractAIModel.
        """
        self.load_weights(model_path=None)

    def load_weights(self, model_path: str | None = None) -> None:
        """
        Load the model weights and initialize the SegFormer architecture.

        Args:
            model_path: Optional explicit path or identifier. Defaults to
                the model_id from metadata if not provided.

        Raises:
            ModelLoadError: If the model fails to load.
        """
        if self.mock_mode:
            logger.info("Mock mode: skipping weight loading.")
            self._model = "mock_model_initialized"
            return

        try:
            from transformers import SegformerForSemanticSegmentation

            path = model_path or self._metadata.model_id
            logger.info(f"Loading SegFormer model from: {path}")

            self._model = SegformerForSemanticSegmentation.from_pretrained(path)
            self._model.to(self._device)
            self._model.eval()
            logger.info(f"SegFormer model loaded successfully to {self._device}.")
        except Exception as e:
            model_id = model_path or self._metadata.model_id
            logger.error(f"Failed to load SegFormer weights from {model_id}: {e}")
            raise ModelLoadError(f"Failed to load SegFormer model: {e}") from e

    def predict(
        self, preprocessed_data: Any, parameters: dict[str, Any] | None = None
    ) -> Any:
        """
        Execute forward inference on the input tensor.

        Args:
            preprocessed_data: A normalized PyTorch tensor representing the input
                imagery.
            parameters: Dynamic inference parameters.

        Returns:
            Raw logits tensor.

        Raises:
            InferenceExecutionError: If inference fails or model is not loaded.
        """
        if self.mock_mode:
            if self._model is None:
                raise InferenceExecutionError(
                    "Model not loaded. Call load_weights() first."
                )

            import torch

            # Deterministic mock tensor having a dummy expected output shape
            return torch.ones((1, 150, 512, 512), dtype=torch.float32)

        if self._model is None:
            raise InferenceExecutionError(
                "Model is not loaded. Call load_weights() first."
            )

        try:
            import torch

            if not isinstance(preprocessed_data, torch.Tensor):
                raise InferenceExecutionError("Input data must be a PyTorch tensor")

            # Move input to the same device as the model
            input_tensor = preprocessed_data.to(self._device)

            with torch.no_grad():
                outputs = self._model(pixel_values=input_tensor)
                return outputs.logits
        except Exception as e:
            logger.error(f"Inference execution failed: {e}")
            raise InferenceExecutionError(f"Inference execution failed: {e}") from e
