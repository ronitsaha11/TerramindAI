from enum import StrEnum


class JobStatus(StrEnum):
    """
    Represents the lifecycle state of an asynchronous job.
    """

    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    STARTED = "STARTED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    CANCELLED = "CANCELLED"
