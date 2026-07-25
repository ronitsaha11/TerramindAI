import abc

import numpy as np


class SpectralIndex(abc.ABC):
    """
    Abstract interface for Earth Observation spectral indices.
    Implementations must be stateless and vectorized using pure NumPy.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """The canonical name of the index (e.g., 'NDVI')."""
        pass

    @property
    @abc.abstractmethod
    def required_bands(self) -> list[str]:
        """List of standard band names required by this index (e.g., ['RED', 'NIR'])."""
        pass

    @abc.abstractmethod
    def compute(self, bands: dict[str, np.ndarray]) -> np.ndarray:
        """
        Compute the spectral index.

        Args:
            bands: A dictionary mapping standard band names to 2D NumPy arrays.

        Returns:
            A 2D float32 NumPy array containing the computed index,
            safely handling NaNs.
        """
        pass
