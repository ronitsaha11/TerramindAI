from src.analytics.exceptions import AnalysisValidationError
from src.analytics.statistics.base import StatisticsProvider


class StatisticsRegistry:
    """Registry for dynamically resolving statistics implementations."""

    def __init__(self) -> None:
        self._providers: dict[str, StatisticsProvider] = {}

    def register(self, provider: StatisticsProvider) -> None:
        self._providers[provider.name.upper()] = provider

    def unregister(self, name: str) -> None:
        normalized_name = name.upper()
        if normalized_name in self._providers:
            del self._providers[normalized_name]

    def get(self, name: str) -> StatisticsProvider:
        normalized_name = name.upper()
        if normalized_name not in self._providers:
            raise AnalysisValidationError(
                f"Statistics provider '{name}' is not registered."
            )
        return self._providers[normalized_name]

    def get_all(self) -> list[StatisticsProvider]:
        return list(self._providers.values())
