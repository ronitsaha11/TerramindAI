from pydantic import BaseModel


class HistogramResult(BaseModel):
    frequencies: list[int]
    bin_edges: list[float]


class PercentileResult(BaseModel):
    p5: float | None = None
    p25: float | None = None
    p50: float | None = None
    p75: float | None = None
    p95: float | None = None


class StatisticsSummary(BaseModel):
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    median: float | None = None
    variance: float | None = None
    std_dev: float | None = None
    valid_pixels: int
    nodata_pixels: int
    nodata_percentage: float
    finite_pixels: int
    histogram: HistogramResult | None = None
    percentiles: PercentileResult | None = None
