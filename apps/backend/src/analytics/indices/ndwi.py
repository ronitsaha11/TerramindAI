import numpy as np

from src.analytics.indices.base import SpectralIndex
from src.analytics.indices.utils import clip_output, safe_divide


class NDWIIndex(SpectralIndex):
    """
    Normalized Difference Water Index.
    Formula: (GREEN - NIR) / (GREEN + NIR)
    Range: [-1.0, 1.0]
    """

    @property
    def name(self) -> str:
        return "NDWI"

    @property
    def required_bands(self) -> list[str]:
        return ["GREEN", "NIR"]

    def compute(self, bands: dict[str, np.ndarray]) -> np.ndarray:
        green = bands["GREEN"]
        nir = bands["NIR"]

        num = green - nir
        den = green + nir

        result = safe_divide(num, den)
        return clip_output(result, -1.0, 1.0)
