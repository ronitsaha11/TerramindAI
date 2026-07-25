from typing import Any

import numpy as np

from src.analytics.exceptions import AnalysisValidationError
from src.analytics.statistics.registry import StatisticsRegistry
from src.analytics.statistics.schemas import StatisticsSummary


class StatisticsEngine:
    """
    Orchestrates registered statistics providers to build a complete summary.
    """

    def __init__(self, registry: StatisticsRegistry) -> None:
        self.registry = registry

    def compute_statistics(self, arr: np.ndarray, bins: int = 10) -> StatisticsSummary:
        """
        Compute statistics across all registered providers and build the summary.
        """
        if not np.issubdtype(arr.dtype, np.number):
            raise AnalysisValidationError(
                "Array must be numeric for statistics computation."
            )

        summary_data: dict[str, Any] = {}

        for provider in self.registry.get_all():
            results = provider.compute(arr, bins=bins)
            summary_data.update(results)

        return StatisticsSummary(**summary_data)
