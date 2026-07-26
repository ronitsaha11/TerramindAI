import pytest

from src.ai.base import AbstractAIModel
from src.ai.exceptions import (
    DuplicateModelRegistrationError,
    ModelLoadError,
    ModelNotFoundError,
)
from src.ai.loader import AIModelLoader
from src.ai.manager import ModelManager
from src.ai.models import ModelMetadata
from src.ai.registry import ModelRegistry


class MockModel(AbstractAIModel):
    def __init__(self) -> None:
        self.is_loaded = False
        self.is_unloaded = False

    @property
    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            model_id="mock-1",
            name="Mock Model",
            version="1.0",
            supported_bands=["RED"],
        )

    def load(self) -> None:
        self.is_loaded = True

    def unload(self) -> None:
        self.is_unloaded = True

    def predict(self, preprocessed_data: any, parameters: dict) -> any:  # type: ignore
        pass


class FailingMockModel(MockModel):
    def load(self) -> None:
        raise ValueError("Simulated load failure")


def test_registry_registration_and_lookup() -> None:
    registry = ModelRegistry()
    meta = MockModel().metadata
    registry.register(meta, MockModel)

    assert len(registry.list_models()) == 1

    fetched_meta, fetched_class = registry.lookup("mock-1")
    assert fetched_meta.model_id == "mock-1"
    assert fetched_class is MockModel


def test_registry_duplicate_registration() -> None:
    registry = ModelRegistry()
    meta = MockModel().metadata
    registry.register(meta, MockModel)

    with pytest.raises(DuplicateModelRegistrationError):
        registry.register(meta, MockModel)


def test_registry_model_not_found() -> None:
    registry = ModelRegistry()
    with pytest.raises(ModelNotFoundError):
        registry.lookup("non-existent")


def test_registry_deregister() -> None:
    registry = ModelRegistry()
    meta = MockModel().metadata
    registry.register(meta, MockModel)
    registry.deregister("mock-1")

    assert len(registry.list_models()) == 0


def test_loader_metadata_validation() -> None:
    loader = AIModelLoader()
    valid_dict = {
        "model_id": "test",
        "name": "Test",
        "version": "1.0",
        "supported_bands": ["RED"],
    }
    meta = loader.load_metadata(valid_dict)
    assert meta.model_id == "test"

    with pytest.raises(ModelLoadError):
        loader.load_metadata({"missing": "fields"})


def test_loader_initialize_provider() -> None:
    loader = AIModelLoader()
    model = loader.initialize_provider(MockModel)
    assert isinstance(model, MockModel)
    assert model.is_loaded is True


def test_loader_initialize_provider_failure() -> None:
    loader = AIModelLoader()
    with pytest.raises(ModelLoadError, match="Simulated load failure"):
        loader.initialize_provider(FailingMockModel)


def test_loader_verify_compatibility() -> None:
    loader = AIModelLoader()

    class IncompatibleModel:
        pass

    with pytest.raises(ModelLoadError):
        loader.initialize_provider(IncompatibleModel)  # type: ignore


def test_manager_lazy_loading_and_cache_reuse() -> None:
    registry = ModelRegistry()
    loader = AIModelLoader()
    manager = ModelManager(registry, loader)

    meta = MockModel().metadata
    registry.register(meta, MockModel)

    # Lazy load
    model1 = manager.get_model("mock-1")
    assert isinstance(model1, MockModel)
    assert model1.is_loaded is True

    # Cache reuse
    model2 = manager.get_model("mock-1")
    assert model1 is model2
    assert manager.loaded_models() == ["mock-1"]


def test_manager_unload_model() -> None:
    registry = ModelRegistry()
    loader = AIModelLoader()
    manager = ModelManager(registry, loader)

    meta = MockModel().metadata
    registry.register(meta, MockModel)

    model = manager.get_model("mock-1")
    manager.unload_model("mock-1")

    assert isinstance(model, MockModel)
    assert model.is_unloaded is True
    assert "mock-1" not in manager.loaded_models()


def test_manager_unload_all() -> None:
    registry = ModelRegistry()
    loader = AIModelLoader()
    manager = ModelManager(registry, loader)

    meta = MockModel().metadata
    registry.register(meta, MockModel)

    model = manager.get_model("mock-1")
    manager.unload_all()

    assert isinstance(model, MockModel)
    assert model.is_unloaded is True
    assert len(manager.loaded_models()) == 0
