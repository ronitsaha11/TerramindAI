import enum

class ProjectStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class JobType(str, enum.Enum):
    SEGMENTATION = "SEGMENTATION"
    CHANGE_DETECTION = "CHANGE_DETECTION"
    FOREST_ANALYSIS = "FOREST_ANALYSIS"
    DATA_IMPORT = "DATA_IMPORT"
    REPORT_GENERATION = "REPORT_GENERATION"

class PredictionType(str, enum.Enum):
    SEGMENTATION_MASK = "SEGMENTATION_MASK"
    CHANGE_MAP = "CHANGE_MAP"
    VEGETATION_INDEX = "VEGETATION_INDEX"

class ReportFormat(str, enum.Enum):
    PDF = "PDF"
    JSON = "JSON"
    CSV = "CSV"

class AuditResourceType(str, enum.Enum):
    PROJECT = "PROJECT"
    REGION = "REGION"
    JOB = "JOB"
    PREDICTION = "PREDICTION"
    REPORT = "REPORT"
