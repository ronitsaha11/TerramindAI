from abc import ABC, abstractmethod
from typing import Any

from src.ai.models import InferenceRequest, InferenceResult, ModelMetadata


class AbstractPreprocessor(ABC):
    """
    Contract for preprocessing raw input data into model-ready tensors.
    """

    @abstractmethod
    def preprocess(self, request: InferenceRequest, raw_data: Any) -> Any:
        """
        Preprocess raw data.

        Args:
            request: The inference request containing parameters.
            raw_data: The raw input data (e.g., NumPy arrays from the RasterProvider).

        Returns:
            Preprocessed data ready for model ingestion (e.g., PyTorch tensors).
            The exact type depends on the framework, hence Any.

        Raises:
            PreprocessingError: If preprocessing fails.
        """
        pass


class AbstractPostprocessor(ABC):
    """
    Contract for converting raw model outputs into standardized InferenceResult data.
    """

    @abstractmethod
    def postprocess(
        self, request: InferenceRequest, model_output: Any
    ) -> dict[str, Any]:
        """
        Postprocess model output.

        Args:
            request: The inference request containing parameters.
            model_output: The raw output from the AI model.

        Returns:
            A dictionary of standardized output data (e.g., extracted polygons,
            statistics) that will populate the InferenceResult.result_data.

        Raises:
            PostprocessingError: If postprocessing fails.
        """
        pass


class AbstractAIModel(ABC):
    """
    Contract for a deployable AI model.
    """

    @property
    @abstractmethod
    def metadata(self) -> ModelMetadata:
        """
        Get the metadata for this model.
        """
        pass

    @abstractmethod
    def load(self) -> None:
        """
        Load the model into memory/VRAM.

        Raises:
            ModelLoadError: If loading fails.
        """
        pass

    @abstractmethod
    def predict(self, preprocessed_data: Any, parameters: dict[str, Any]) -> Any:
        """
        Execute inference on preprocessed data.

        Args:
            preprocessed_data: The output from an AbstractPreprocessor.
            parameters: Dynamic inference parameters.

        Returns:
            Raw model outputs.

        Raises:
            InferenceExecutionError: If inference fails.
        """
        pass


class AbstractInferenceProvider(ABC):
    """
    Contract for the overarching AI execution engine that orchestrates
    preprocessing, model execution, and postprocessing.
    """

    @abstractmethod
    async def execute_inference(self, request: InferenceRequest) -> InferenceResult:
        """
        Execute the full inference pipeline.

        Args:
            request: The inference request payload.

        Returns:
            The final standardized inference result.

        Raises:
            ModelNotFoundError: If the requested model is not available.
            InferenceValidationError: If the request is invalid.
            InferenceExecutionError: If any step of the pipeline fails unexpectedly.
        """
        pass
