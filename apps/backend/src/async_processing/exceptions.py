from src.core.exceptions import AppException


class AsyncProcessingError(AppException):
    """Base exception for all asynchronous processing errors."""

    def __init__(
        self, detail: str = "Asynchronous processing error", status_code: int = 500
    ) -> None:
        super().__init__(detail=detail, status_code=status_code)


class JobNotFoundError(AsyncProcessingError):
    """Raised when a requested job cannot be found in the store."""

    def __init__(self, detail: str = "Job not found") -> None:
        super().__init__(detail=detail, status_code=404)


class JobStateError(AsyncProcessingError):
    """Raised when an invalid job lifecycle transition is attempted."""

    def __init__(self, detail: str = "Invalid job state transition") -> None:
        super().__init__(detail=detail, status_code=409)


class DuplicateTaskError(AsyncProcessingError):
    """Raised when attempting to register a task name that already exists."""

    def __init__(self, detail: str = "Task name already registered") -> None:
        super().__init__(detail=detail, status_code=409)


class TaskExecutionError(AsyncProcessingError):
    """Raised when a task fails during execution."""

    def __init__(self, detail: str = "Task execution failed") -> None:
        super().__init__(detail=detail, status_code=500)


class JobSubmissionError(AsyncProcessingError):
    """Raised when a job fails to submit properly."""

    def __init__(self, detail: str = "Job submission failed") -> None:
        super().__init__(detail=detail, status_code=400)


class JobCancellationError(AsyncProcessingError):
    """Raised when a job cancellation request is invalid."""

    def __init__(self, detail: str = "Job cancellation failed") -> None:
        super().__init__(detail=detail, status_code=400)


class JobRetryError(AsyncProcessingError):
    """Raised when a job retry request is invalid."""

    def __init__(self, detail: str = "Job retry failed") -> None:
        super().__init__(detail=detail, status_code=400)


class UnknownJobError(JobNotFoundError):
    """Raised when querying a job that does not exist (alias of JobNotFoundError)."""

    pass


class InvalidJobOperationError(AsyncProcessingError):
    """Raised when attempting an operation not supported by the job's current state."""

    def __init__(self, detail: str = "Invalid job operation") -> None:
        super().__init__(detail=detail, status_code=400)
