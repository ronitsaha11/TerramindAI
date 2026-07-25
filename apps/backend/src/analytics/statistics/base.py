import abc
from typing import Any

import numpy as np


class StatisticsProvider(abc.ABC):
    """
    Abstract interface for Earth Observation statistical metrics.
    Implementations must be stateless and operate safely on NumPy arrays.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """The canonical name of the statistical metric or provider group."""
        pass

    @abc.abstractmethod
    def compute(self, arr: np.ndarray, **kwargs: Any) -> dict[str, Any]:
        """
        Compute statistical metrics.

        Args:
            arr: 2D NumPy array containing the Earth Observation index or band data.
            **kwargs: Extra configuration (e.g. number of bins for histograms).

        Returns:
            Dictionary containing computed metric keys and values.
        """
        pass
