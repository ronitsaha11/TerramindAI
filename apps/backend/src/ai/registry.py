import threading

from src.ai.base import AbstractAIModel
from src.ai.exceptions import DuplicateModelRegistrationError, ModelNotFoundError
from src.ai.models import ModelMetadata


class ModelRegistry:
    """Registry for managing available AI models and their metadata."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._models: dict[str, tuple[ModelMetadata, type[AbstractAIModel]]] = {}

    def register(
        self, metadata: ModelMetadata, provider_class: type[AbstractAIModel]
    ) -> None:
        """Register a new model.

        Args:
            metadata: The model's metadata.
            provider_class: The class implementing AbstractAIModel.

        Raises:
            DuplicateModelRegistrationError: If model_id is already registered.
        """
        with self._lock:
            if metadata.model_id in self._models:
                raise DuplicateModelRegistrationError(
                    f"Model {metadata.model_id} is already registered."
                )
            self._models[metadata.model_id] = (metadata, provider_class)

    def lookup(self, model_id: str) -> tuple[ModelMetadata, type[AbstractAIModel]]:
        """Retrieve model metadata and provider class.

        Args:
            model_id: The identifier of the model.

        Returns:
            A tuple of (ModelMetadata, type[AbstractAIModel]).

        Raises:
            ModelNotFoundError: If model_id is not registered.
        """
        with self._lock:
            if model_id not in self._models:
                raise ModelNotFoundError(f"Model {model_id} not found in registry.")
            return self._models[model_id]

    def deregister(self, model_id: str) -> None:
        """Remove a model from the registry.

        Args:
            model_id: The identifier of the model.
        """
        with self._lock:
            self._models.pop(model_id, None)

    def list_models(self) -> list[ModelMetadata]:
        """List metadata of all registered models.

        Returns:
            A list of ModelMetadata objects.
        """
        with self._lock:
            return [metadata for metadata, _ in self._models.values()]
