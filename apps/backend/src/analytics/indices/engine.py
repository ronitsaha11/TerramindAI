import numpy as np

from src.analytics.exceptions import AnalysisValidationError
from src.analytics.indices.base import SpectralIndex
from src.analytics.indices.registry import IndexRegistry


class IndexEngine:
    """
    Orchestrates the computation of spectral indices.
    Resolves implementations via the registry and validates input tensors.
    """

    def __init__(self, registry: IndexRegistry) -> None:
        self.registry = registry

    def compute(self, index_name: str, bands: dict[str, np.ndarray]) -> np.ndarray:
        """
        Compute a spectral index given a dictionary of raw band arrays.

        Args:
            index_name: The registered name of the index (e.g., 'NDVI').
            bands: Dictionary of NumPy arrays corresponding to band data.

        Returns:
            The computed index as a float32 NumPy array.
        """
        # Resolve index
        index: SpectralIndex = self.registry.get(index_name)

        # Validate required bands exist
        for required_band in index.required_bands:
            if required_band not in bands:
                raise AnalysisValidationError(
                    f"Index '{index_name}' requires band '{required_band}', "
                    "which was not provided."
                )

        # Validate shapes match
        expected_shape = None
        for required_band in index.required_bands:
            arr = bands[required_band]
            if expected_shape is None:
                expected_shape = arr.shape
            elif arr.shape != expected_shape:
                raise AnalysisValidationError(
                    f"Shape mismatch for band '{required_band}'. "
                    f"Expected {expected_shape}, got {arr.shape}."
                )

        # Execute pure math
        return index.compute(bands)
