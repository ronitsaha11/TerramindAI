import pytest

from src.analytics.providers.cog_provider import COGRasterProvider
from src.api.dependencies import get_analytics_engine, get_raster_provider


def test_get_raster_provider() -> None:
    provider = get_raster_provider()
    assert isinstance(provider, COGRasterProvider)


def test_get_analytics_engine() -> None:
    with pytest.raises(NotImplementedError, match="AnalyticsEngine not yet implemented"):
        get_analytics_engine()
