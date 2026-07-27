import pytest

from src.async_processing.exceptions import DuplicateTaskError, JobNotFoundError
from src.async_processing.registry import TaskRegistry


@pytest.fixture
def registry() -> TaskRegistry:
    return TaskRegistry()


def dummy_task() -> None:
    pass


def test_registry_registration(registry: TaskRegistry) -> None:
    registry.register("dummy", dummy_task)
    func = registry.lookup("dummy")
    assert func is dummy_task


def test_registry_duplicate_registration_rejected(registry: TaskRegistry) -> None:
    registry.register("dummy", dummy_task)
    with pytest.raises(DuplicateTaskError, match="is already registered"):
        registry.register("dummy", dummy_task)


def test_registry_lookup_not_found(registry: TaskRegistry) -> None:
    with pytest.raises(JobNotFoundError, match="is not registered"):
        registry.lookup("non_existent")


def test_registry_clear(registry: TaskRegistry) -> None:
    registry.register("dummy", dummy_task)
    registry.clear()
    with pytest.raises(JobNotFoundError):
        registry.lookup("dummy")
