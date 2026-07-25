import numpy as np
import pytest

from src.analytics.exceptions import AnalysisValidationError
from src.analytics.statistics.engine import StatisticsEngine
from src.analytics.statistics.metrics import (
    CoreStatisticsProvider,
    HistogramProvider,
    PercentileProvider,
)
from src.analytics.statistics.registry import StatisticsRegistry
from src.analytics.statistics.utils import is_all_nan


@pytest.fixture
def engine():
    registry = StatisticsRegistry()
    registry.register(CoreStatisticsProvider())
    registry.register(PercentileProvider())
    registry.register(HistogramProvider())
    return StatisticsEngine(registry)


def test_is_all_nan():
    assert is_all_nan(np.array([np.nan, np.nan])) is True
    assert is_all_nan(np.array([1.0, np.nan])) is False
    assert is_all_nan(np.array([])) is True


def test_registry_operations():
    registry = StatisticsRegistry()
    provider = CoreStatisticsProvider()

    registry.register(provider)
    assert "CORE" in [p.name for p in registry.get_all()]

    retrieved = registry.get("CORE")
    assert retrieved is provider

    with pytest.raises(AnalysisValidationError):
        registry.get("UNKNOWN")

    registry.unregister("CORE")
    assert len(registry.get_all()) == 0


def test_normal_array(engine):
    arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
    summary = engine.compute_statistics(arr, bins=2)

    assert summary.min == 1.0
    assert summary.max == 5.0
    assert summary.mean == 3.0
    assert summary.median == 3.0
    assert summary.valid_pixels == 5
    assert summary.nodata_pixels == 0
    assert summary.finite_pixels == 5

    assert summary.percentiles is not None
    assert summary.percentiles.p50 == 3.0

    assert summary.histogram is not None
    assert len(summary.histogram.frequencies) == 2


def test_negative_values(engine):
    arr = np.array([-5.0, -1.0, 0.0], dtype=np.float32)
    summary = engine.compute_statistics(arr)

    assert summary.min == -5.0
    assert summary.max == 0.0


def test_mixed_nan_array(engine):
    arr = np.array([1.0, np.nan, 3.0, np.nan, 5.0], dtype=np.float32)
    summary = engine.compute_statistics(arr)

    assert summary.min == 1.0
    assert summary.max == 5.0
    assert summary.mean == 3.0
    assert summary.valid_pixels == 3
    assert summary.nodata_pixels == 2
    assert summary.nodata_percentage == 40.0


def test_all_nan_array(engine):
    arr = np.array([np.nan, np.nan, np.nan], dtype=np.float32)
    summary = engine.compute_statistics(arr)

    assert summary.min is None
    assert summary.max is None
    assert summary.mean is None
    assert summary.valid_pixels == 0
    assert summary.nodata_pixels == 3
    assert summary.nodata_percentage == 100.0

    assert summary.percentiles is not None
    assert summary.percentiles.p50 is None

    assert summary.histogram is None


def test_empty_array(engine):
    arr = np.array([], dtype=np.float32)
    summary = engine.compute_statistics(arr)

    assert summary.min is None
    assert summary.valid_pixels == 0
    assert summary.nodata_pixels == 0
    assert summary.histogram is None


def test_large_array(engine):
    # 1000x1000 random array (1M pixels)
    arr = np.random.rand(1000, 1000).astype(np.float32)
    # Should not crash, and execute quickly
    summary = engine.compute_statistics(arr)

    assert summary.valid_pixels == 1000000
    assert summary.nodata_pixels == 0
    assert summary.min is not None


def test_validation_failure(engine):
    # Pass a non-numeric array
    arr = np.array(["a", "b", "c"])
    with pytest.raises(AnalysisValidationError, match="numeric"):
        engine.compute_statistics(arr)
