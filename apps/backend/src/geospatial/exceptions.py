from src.core.exceptions import AppException


class GeospatialProcessingError(AppException):
    """Base exception for geospatial processing errors."""

    def __init__(
        self,
        detail: str = "A geospatial processing error occurred",
        status_code: int = 500,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)


class PolygonizationError(GeospatialProcessingError):
    """Raised when polygonization of a raster fails."""

    def __init__(self, detail: str = "Polygonization failed") -> None:
        super().__init__(detail=detail, status_code=500)


class TransformValidationError(GeospatialProcessingError):
    """Raised when an invalid affine transform is provided."""

    def __init__(self, detail: str = "Invalid affine transform") -> None:
        super().__init__(detail=detail, status_code=400)


class GeometryProcessingError(GeospatialProcessingError):
    """Raised when geometry processing fails."""

    def __init__(self, detail: str = "Geometry processing failed") -> None:
        super().__init__(detail=detail, status_code=500)


class GeometryValidationError(GeometryProcessingError):
    """Raised when an invalid geometry is encountered or a validation fails."""

    def __init__(self, detail: str = "Geometry validation failed") -> None:
        super().__init__(detail=detail)


class SpatialAnalyticsError(GeospatialProcessingError):
    """Raised when spatial analytics fails."""

    def __init__(self, detail: str = "Spatial analytics failed") -> None:
        super().__init__(detail=detail, status_code=500)


class AnalyticsValidationError(SpatialAnalyticsError):
    """Raised when an analytics validation constraint fails."""

    def __init__(self, detail: str = "Analytics validation failed") -> None:
        super().__init__(detail=detail)


class ProjectionError(SpatialAnalyticsError):
    """Raised when a geometry projection operation fails."""

    def __init__(self, detail: str = "Projection failed") -> None:
        super().__init__(detail=detail)
