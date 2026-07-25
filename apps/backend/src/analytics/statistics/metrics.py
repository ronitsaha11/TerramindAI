from typing import Any

import numpy as np

from src.analytics.statistics.base import StatisticsProvider
from src.analytics.statistics.schemas import HistogramResult, PercentileResult
from src.analytics.statistics.utils import get_finite_mask, get_valid_mask, is_all_nan


class CoreStatisticsProvider(StatisticsProvider):
    @property
    def name(self) -> str:
        return "CORE"

    def compute(self, arr: np.ndarray, **kwargs: Any) -> dict[str, Any]:
        total_pixels = arr.size
        if total_pixels == 0:
            return {
                "min": None,
                "max": None,
                "mean": None,
                "median": None,
                "variance": None,
                "std_dev": None,
                "valid_pixels": 0,
                "nodata_pixels": 0,
                "nodata_percentage": 0.0,
                "finite_pixels": 0,
            }

        valid_mask = get_valid_mask(arr)
        valid_pixels = int(np.sum(valid_mask))
        nodata_pixels = total_pixels - valid_pixels
        nodata_percentage = (nodata_pixels / total_pixels) * 100.0
        finite_pixels = int(np.sum(get_finite_mask(arr)))

        # All-NaN Policy short-circuit
        if is_all_nan(arr):
            return {
                "min": None,
                "max": None,
                "mean": None,
                "median": None,
                "variance": None,
                "std_dev": None,
                "valid_pixels": valid_pixels,
                "nodata_pixels": nodata_pixels,
                "nodata_percentage": nodata_percentage,
                "finite_pixels": finite_pixels,
            }

        with np.errstate(invalid="ignore", divide="ignore"):
            _min = float(np.nanmin(arr))
            _max = float(np.nanmax(arr))
            _mean = float(np.nanmean(arr))
            _median = float(np.nanmedian(arr))
            _var = float(np.nanvar(arr))
            _std = float(np.nanstd(arr))

        return {
            "min": _min,
            "max": _max,
            "mean": _mean,
            "median": _median,
            "variance": _var,
            "std_dev": _std,
            "valid_pixels": valid_pixels,
            "nodata_pixels": nodata_pixels,
            "nodata_percentage": nodata_percentage,
            "finite_pixels": finite_pixels,
        }


class PercentileProvider(StatisticsProvider):
    @property
    def name(self) -> str:
        return "PERCENTILES"

    def compute(self, arr: np.ndarray, **kwargs: Any) -> dict[str, Any]:
        if arr.size == 0 or is_all_nan(arr):
            return {"percentiles": PercentileResult()}

        with np.errstate(invalid="ignore", divide="ignore"):
            p5, p25, p50, p75, p95 = np.nanpercentile(arr, [5, 25, 50, 75, 95])

        return {
            "percentiles": PercentileResult(
                p5=float(p5),
                p25=float(p25),
                p50=float(p50),
                p75=float(p75),
                p95=float(p95),
            )
        }


class HistogramProvider(StatisticsProvider):
    @property
    def name(self) -> str:
        return "HISTOGRAM"

    def compute(self, arr: np.ndarray, **kwargs: Any) -> dict[str, Any]:
        if arr.size == 0 or is_all_nan(arr):
            return {"histogram": None}

        bins = kwargs.get("bins", 10)

        # Only compute histogram on finite pixels
        finite_arr = arr[get_finite_mask(arr)]
        if finite_arr.size == 0:
            return {"histogram": None}

        freqs, edges = np.histogram(finite_arr, bins=bins)

        return {
            "histogram": HistogramResult(
                frequencies=freqs.tolist(),
                bin_edges=edges.tolist(),
            )
        }
