import pytest

from src.api.dependencies import get_analytics_engine, get_raster_provider


def test_get_raster_provider() -> None:
    with pytest.raises(NotImplementedError, match="RasterProvider not yet implemented"):
        get_raster_provider()


def test_get_analytics_engine() -> None:
    with pytest.raises(
        NotImplementedError, match="AnalyticsEngine not yet implemented"
    ):
        get_analytics_engine()
