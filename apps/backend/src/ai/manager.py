import threading

from src.ai.base import AbstractAIModel
from src.ai.loader import AIModelLoader
from src.ai.registry import ModelRegistry


class ModelManager:
    """Manages the lifecycle of AI models including lazy loading and caching."""

    def __init__(self, registry: ModelRegistry, loader: AIModelLoader) -> None:
        """Initialize the ModelManager.

        Args:
            registry: The registry to lookup models.
            loader: The loader to initialize models.
        """
        self._registry = registry
        self._loader = loader
        self._lock = threading.Lock()
        self._cache: dict[str, AbstractAIModel] = {}

    def get_model(self, model_id: str) -> AbstractAIModel:
        """Retrieve a loaded model instance, lazy loading if necessary.

        Args:
            model_id: The identifier of the model.

        Returns:
            The loaded model instance.

        Raises:
            ModelNotFoundError: If the model is not registered.
            ModelLoadError: If the model fails to load.
        """
        with self._lock:
            if model_id in self._cache:
                return self._cache[model_id]

            # Lazy load
            _, provider_class = self._registry.lookup(model_id)
            model_instance = self._loader.initialize_provider(provider_class)
            self._cache[model_id] = model_instance
            return model_instance

    def unload_model(self, model_id: str) -> None:
        """Unload a specific model from memory.

        Args:
            model_id: The identifier of the model to unload.
        """
        with self._lock:
            if model_id in self._cache:
                model_instance = self._cache.pop(model_id)
                self._loader.unload(model_instance)

    def unload_all(self) -> None:
        """Unload all cached models."""
        with self._lock:
            for model_instance in self._cache.values():
                self._loader.unload(model_instance)
            self._cache.clear()

    def loaded_models(self) -> list[str]:
        """Get a list of currently loaded model IDs.

        Returns:
            A list of model IDs.
        """
        with self._lock:
            return list(self._cache.keys())
