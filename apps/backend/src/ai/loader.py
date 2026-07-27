from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.ai.base import AbstractAIModel
from src.ai.exceptions import ModelLoadError
from src.ai.models import ModelMetadata


class AIModelLoader:
    """Handles physical validation and initialization of AI models."""

    def validate_path(self, path: Path | str) -> bool:
        """Verify model files exist.

        Args:
            path: Path to the model directory or file.

        Returns:
            True if the path exists.

        Raises:
            ModelLoadError: If the path does not exist.
        """
        p = Path(path)
        if not p.exists():
            raise ModelLoadError(f"Model path does not exist: {path}")
        return True

    def load_metadata(self, metadata_dict: dict[str, Any]) -> ModelMetadata:
        """Parse and validate model metadata.

        Args:
            metadata_dict: Raw dictionary containing metadata fields.

        Returns:
            A validated ModelMetadata instance.

        Raises:
            ModelLoadError: If metadata validation fails.
        """
        try:
            return ModelMetadata(**metadata_dict)
        except ValidationError as e:
            raise ModelLoadError(f"Invalid model metadata: {e}") from e

    def verify_compatibility(self, provider_class: type) -> bool:
        """Verify that the provider class implements AbstractAIModel.

        Args:
            provider_class: The class to check.

        Returns:
            True if compatible.

        Raises:
            ModelLoadError: If the provider class is incompatible.
        """
        if not issubclass(provider_class, AbstractAIModel):
            raise ModelLoadError(
                f"Provider {provider_class.__name__} does not "
                "implement AbstractAIModel."
            )
        return True

    def initialize_provider(
        self, provider_class: type[AbstractAIModel], metadata: ModelMetadata
    ) -> AbstractAIModel:
        """Instantiate the model class and load it.

        Args:
            provider_class: The model class to initialize.

        Returns:
            The initialized and loaded model instance.

        Raises:
            ModelLoadError: If initialization or loading fails.
        """
        self.verify_compatibility(provider_class)
        try:
            model = provider_class(metadata=metadata)
            model.load()
            return model
        except Exception as e:
            # Re-raise AI exceptions directly to avoid wrapping
            from src.ai.exceptions import AIException

            if isinstance(e, AIException):
                raise
            raise ModelLoadError(
                f"Failed to initialize model {provider_class.__name__}: {e}"
            ) from e

    def unload(self, model: AbstractAIModel) -> None:
        """Safely dispose of a model.

        Args:
            model: The model instance to unload.
        """
        # If the model has an explicit unload method, call it.
        if hasattr(model, "unload") and callable(model.unload):
            try:
                model.unload()
            except Exception:
                pass

    def get_model_info(self, model: AbstractAIModel) -> ModelMetadata:
        """Expose model information.

        Args:
            model: The loaded model instance.

        Returns:
            The model's metadata.
        """
        return model.metadata
