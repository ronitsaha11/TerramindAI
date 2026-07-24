import enum


class ProjectStatus(enum.StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class JobStatus(enum.StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobType(enum.StrEnum):
    SEGMENTATION = "SEGMENTATION"
    CHANGE_DETECTION = "CHANGE_DETECTION"
    FOREST_ANALYSIS = "FOREST_ANALYSIS"
    DATA_IMPORT = "DATA_IMPORT"
    REPORT_GENERATION = "REPORT_GENERATION"


class PredictionType(enum.StrEnum):
    SEGMENTATION_MASK = "SEGMENTATION_MASK"
    CHANGE_MAP = "CHANGE_MAP"
    VEGETATION_INDEX = "VEGETATION_INDEX"


class ReportFormat(enum.StrEnum):
    PDF = "PDF"
    JSON = "JSON"
    CSV = "CSV"


class AuditResourceType(enum.StrEnum):
    PROJECT = "PROJECT"
    REGION = "REGION"
    JOB = "JOB"
    PREDICTION = "PREDICTION"
    REPORT = "REPORT"
