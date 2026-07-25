import numpy as np

from src.analytics.indices.base import SpectralIndex
from src.analytics.indices.utils import clip_output, safe_divide


class NDVIIndex(SpectralIndex):
    """
    Normalized Difference Vegetation Index.
    Formula: (NIR - RED) / (NIR + RED)
    Range: [-1.0, 1.0]
    """

    @property
    def name(self) -> str:
        return "NDVI"

    @property
    def required_bands(self) -> list[str]:
        return ["NIR", "RED"]

    def compute(self, bands: dict[str, np.ndarray]) -> np.ndarray:
        nir = bands["NIR"]
        red = bands["RED"]

        num = nir - red
        den = nir + red

        result = safe_divide(num, den)
        return clip_output(result, -1.0, 1.0)
