class AIException(Exception):
    """Base exception for all AI operations."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ModelLoadError(AIException):
    """Raised when an AI model fails to load."""


class InferenceExecutionError(AIException):
    """Raised when an error occurs during model inference."""


class PreprocessingError(AIException):
    """Raised when data preprocessing fails."""


class PostprocessingError(AIException):
    """Raised when model output postprocessing fails."""


class ModelNotFoundError(AIException):
    """Raised when a requested AI model cannot be found in the registry or storage."""


class InferenceValidationError(AIException):
    """Raised when an inference request fails validation (e.g., incompatible inputs)."""
