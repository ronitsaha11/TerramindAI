from enum import StrEnum


class ProcessingStatus(StrEnum):
    """Represents the lifecycle status of an analysis request."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisType(StrEnum):
    """The type of analysis to be performed."""

    NDVI = "ndvi"
    NDWI = "ndwi"
    NDBI = "ndbi"
    CUSTOM_INFERENCE = "custom_inference"
