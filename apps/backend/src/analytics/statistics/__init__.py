from src.analytics.statistics.base import StatisticsProvider
from src.analytics.statistics.engine import StatisticsEngine
from src.analytics.statistics.metrics import (
    CoreStatisticsProvider,
    HistogramProvider,
    PercentileProvider,
)
from src.analytics.statistics.registry import StatisticsRegistry
from src.analytics.statistics.schemas import (
    HistogramResult,
    PercentileResult,
    StatisticsSummary,
)
from src.analytics.statistics.utils import is_all_nan

# Pre-configured default registry and engine
default_registry = StatisticsRegistry()
default_registry.register(CoreStatisticsProvider())
default_registry.register(PercentileProvider())
default_registry.register(HistogramProvider())

default_engine = StatisticsEngine(default_registry)

__all__ = [
    "StatisticsProvider",
    "StatisticsRegistry",
    "StatisticsEngine",
    "CoreStatisticsProvider",
    "PercentileProvider",
    "HistogramProvider",
    "StatisticsSummary",
    "HistogramResult",
    "PercentileResult",
    "is_all_nan",
    "default_registry",
    "default_engine",
]
