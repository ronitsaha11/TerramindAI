from src.analytics.exceptions import (
    AnalysisValidationError,
    AnalyticsError,
    InvalidBandError,
    ProviderError,
    RasterMetadataError,
    RasterOpenError,
    RasterReadError,
    StatisticsError,
    UnsupportedRasterError,
)
from src.core.exceptions import AppException


def test_analytics_exception_hierarchy() -> None:
    # Ensure AnalyticsError inherits from AppException
    err = AnalyticsError(status_code=500, detail="Base error")
    assert isinstance(err, AppException)
    assert err.status_code == 500

    # Ensure all specific errors inherit from AnalyticsError
    exceptions = [
        RasterOpenError(),
        RasterReadError(),
        RasterMetadataError(),
        UnsupportedRasterError(),
        InvalidBandError(),
        AnalysisValidationError(),
        StatisticsError(),
        ProviderError(),
    ]

    for exc in exceptions:
        assert isinstance(exc, AnalyticsError)

    # Check a specific status code
    val_err = AnalysisValidationError()
    assert val_err.status_code == 422
