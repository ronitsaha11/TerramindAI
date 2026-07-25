from src.analytics.exceptions import AnalysisValidationError
from src.analytics.indices.base import SpectralIndex


class IndexRegistry:
    """Registry for dynamically resolving spectral index implementations."""

    def __init__(self) -> None:
        self._indices: dict[str, SpectralIndex] = {}

    def register(self, index: SpectralIndex) -> None:
        """Register a new spectral index."""
        self._indices[index.name.upper()] = index

    def unregister(self, name: str) -> None:
        """Unregister an index."""
        normalized_name = name.upper()
        if normalized_name in self._indices:
            del self._indices[normalized_name]

    def get(self, name: str) -> SpectralIndex:
        """Get an index by name. Raises AnalysisValidationError if not found."""
        normalized_name = name.upper()
        if normalized_name not in self._indices:
            raise AnalysisValidationError(f"Spectral index '{name}' is not registered.")
        return self._indices[normalized_name]

    def list(self) -> list[str]:
        """List all registered index names."""
        return list(self._indices.keys())
