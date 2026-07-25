import numpy as np
import pytest

from src.analytics.exceptions import AnalysisValidationError
from src.analytics.indices.base import SpectralIndex
from src.analytics.indices.engine import IndexEngine
from src.analytics.indices.ndvi import NDVIIndex
from src.analytics.indices.ndwi import NDWIIndex
from src.analytics.indices.registry import IndexRegistry
from src.analytics.indices.utils import clip_output, mask_invalid_pixels, safe_divide


# 1. Test Utilities
def test_safe_divide():
    num = np.array([10.0, -10.0, 0.0, np.nan, np.inf], dtype=np.float32)
    den = np.array([2.0, 0.0, 0.0, 1.0, 1.0], dtype=np.float32)

    result = safe_divide(num, den)

    assert result[0] == 5.0
    assert np.isnan(result[1])  # -10 / 0 yields inf -> nan
    assert np.isnan(result[2])  # 0 / 0 yields nan -> nan
    assert np.isnan(result[3])
    assert np.isnan(result[4])  # inf gets safely cast to nan


def test_mask_invalid_pixels():
    arr = np.array([1.0, 2.0, -9999.0, 4.0])
    result = mask_invalid_pixels(arr, nodata=-9999.0)

    assert result[0] == 1.0
    assert np.isnan(result[2])
    assert result.dtype == np.float32


def test_clip_output():
    arr = np.array([-2.0, 0.5, 2.0, np.nan])
    result = clip_output(arr, -1.0, 1.0)

    assert result[0] == -1.0
    assert result[1] == 0.5
    assert result[2] == 1.0
    assert np.isnan(result[3])


# 2. Test NDVI
def test_ndvi_computation():
    index = NDVIIndex()
    # NIR, RED
    # Vegetation: NIR=100, RED=10 -> (100-10)/(100+10) = 90/110 = 0.818
    # Soil: NIR=30, RED=30 -> (30-30)/(30+30) = 0
    # Water: NIR=10, RED=50 -> (10-50)/(10+50) = -40/60 = -0.666
    bands = {
        "NIR": np.array([100.0, 30.0, 10.0, 0.0]),
        "RED": np.array([10.0, 30.0, 50.0, 0.0]),
    }

    result = index.compute(bands)

    assert np.isclose(result[0], 0.818, atol=0.01)
    assert np.isclose(result[1], 0.0)
    assert np.isclose(result[2], -0.666, atol=0.01)
    assert np.isnan(result[3])  # 0/0 is NaN


# 3. Test NDWI
def test_ndwi_computation():
    index = NDWIIndex()
    # GREEN, NIR
    # Water: GREEN=80, NIR=10 -> (80-10)/(80+10) = 70/90 = 0.777
    # Vegetation: GREEN=20, NIR=90 -> (20-90)/(20+90) = -70/110 = -0.636
    bands = {
        "GREEN": np.array([80.0, 20.0, 0.0]),
        "NIR": np.array([10.0, 90.0, 0.0]),
    }

    result = index.compute(bands)

    assert np.isclose(result[0], 0.777, atol=0.01)
    assert np.isclose(result[1], -0.636, atol=0.01)
    assert np.isnan(result[2])  # 0/0


# 4. Test Registry
def test_registry_operations():
    registry = IndexRegistry()
    ndvi = NDVIIndex()

    registry.register(ndvi)
    assert "NDVI" in registry.list()

    retrieved = registry.get("ndvi")
    assert retrieved is ndvi

    with pytest.raises(AnalysisValidationError, match="not registered"):
        registry.get("NDWI")

    registry.unregister("ndvi")
    assert "NDVI" not in registry.list()


# 5. Test Engine Orchestration
class DummyIndex(SpectralIndex):
    @property
    def name(self) -> str:
        return "DUMMY"

    @property
    def required_bands(self) -> list[str]:
        return ["A", "B"]

    def compute(self, bands: dict[str, np.ndarray]) -> np.ndarray:
        return bands["A"] + bands["B"]


def test_engine_missing_bands():
    registry = IndexRegistry()
    registry.register(DummyIndex())
    engine = IndexEngine(registry)

    # Missing band B
    bands = {"A": np.array([1])}

    with pytest.raises(AnalysisValidationError, match="requires band 'B'"):
        engine.compute("DUMMY", bands)


def test_engine_shape_mismatch():
    registry = IndexRegistry()
    registry.register(DummyIndex())
    engine = IndexEngine(registry)

    bands = {"A": np.ones((10, 10)), "B": np.ones((5, 5))}

    with pytest.raises(AnalysisValidationError, match="Shape mismatch"):
        engine.compute("DUMMY", bands)


def test_engine_success():
    registry = IndexRegistry()
    registry.register(DummyIndex())
    engine = IndexEngine(registry)

    bands = {"A": np.ones((2, 2)), "B": np.ones((2, 2)) * 2}

    result = engine.compute("DUMMY", bands)

    assert result.shape == (2, 2)
    assert np.all(result == 3)
