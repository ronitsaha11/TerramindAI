from src.core.exceptions import AppException


class AnalyticsError(AppException):
    """Base exception for all analytics errors."""

    pass


class RasterOpenError(AnalyticsError):
    """Raised when a raster file cannot be opened."""

    def __init__(self, detail: str = "Failed to open raster") -> None:
        super().__init__(status_code=500, detail=detail)


class RasterReadError(AnalyticsError):
    """Raised when data cannot be read from an open raster."""

    def __init__(self, detail: str = "Failed to read raster data") -> None:
        super().__init__(status_code=500, detail=detail)


class RasterMetadataError(AnalyticsError):
    """Raised when raster metadata is missing or invalid."""

    def __init__(self, detail: str = "Invalid or missing raster metadata") -> None:
        super().__init__(status_code=500, detail=detail)


class UnsupportedRasterError(AnalyticsError):
    """Raised when a raster format or capability is not supported."""

    def __init__(self, detail: str = "Unsupported raster format or operation") -> None:
        super().__init__(status_code=400, detail=detail)


class InvalidBandError(AnalyticsError):
    """Raised when an invalid or nonexistent band is requested."""

    def __init__(self, detail: str = "Invalid band requested") -> None:
        super().__init__(status_code=400, detail=detail)


class AnalysisValidationError(AnalyticsError):
    """Raised when an analysis request fails business validation."""

    def __init__(self, detail: str = "Invalid analysis request") -> None:
        super().__init__(status_code=422, detail=detail)


class StatisticsError(AnalyticsError):
    """Raised when statistical computation fails."""

    def __init__(self, detail: str = "Failed to compute statistics") -> None:
        super().__init__(status_code=500, detail=detail)


class ProviderError(AnalyticsError):
    """Raised when an external analytics or raster provider fails."""

    def __init__(self, detail: str = "External provider error") -> None:
        super().__init__(status_code=502, detail=detail)
