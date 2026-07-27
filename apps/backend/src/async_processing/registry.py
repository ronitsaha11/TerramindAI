from collections.abc import Callable
from typing import Any

from src.async_processing.exceptions import DuplicateTaskError, JobNotFoundError


class TaskRegistry:
    """
    In-memory thread-safe singleton for tracking task definitions.
    Decoupled entirely from Celery's internal registry.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]) -> None:
        """
        Register a task callable.

        Args:
            name: The unique string identifier for the task.
            func: The callable task function.

        Raises:
            DuplicateTaskError: If the task name is already registered.
        """
        if name in self._tasks:
            raise DuplicateTaskError(f"Task name '{name}' is already registered.")

        self._tasks[name] = func

    def lookup(self, name: str) -> Callable[..., Any]:
        """
        Lookup a registered task by its name.

        Args:
            name: The unique string identifier for the task.

        Returns:
            The callable task function.

        Raises:
            JobNotFoundError: If the task name is not registered.
        """
        if name not in self._tasks:
            raise JobNotFoundError(f"Task name '{name}' is not registered.")

        return self._tasks[name]

    def clear(self) -> None:
        """Clear all registered tasks (useful for testing)."""
        self._tasks.clear()


# Global Singleton
default_registry = TaskRegistry()
