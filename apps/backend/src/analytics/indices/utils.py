import numpy as np


def safe_divide(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    """
    Safely divide two NumPy arrays.
    Replaces divide-by-zero or NaN results with np.nan.
    Suppresses RuntimeWarnings natively.
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.divide(num, den)
        # Any infinity (due to division by exact zero) becomes NaN
        result[np.isinf(result)] = np.nan
    return result


def mask_invalid_pixels(arr: np.ndarray, nodata: float | None) -> np.ndarray:
    """
    Replaces nodata pixels with np.nan.
    Returns a float32 array for consistent downstream processing.
    """
    result = arr.astype(np.float32, copy=False)
    if nodata is not None:
        # np.isclose handles floating point representation issues safely
        result[np.isclose(result, nodata)] = np.nan
    return result


def clip_output(arr: np.ndarray, min_val: float, max_val: float) -> np.ndarray:
    """
    Clips array values strictly within [min_val, max_val].
    NaN values are perfectly preserved.
    """
    # np.clip automatically preserves NaNs in modern NumPy
    return np.clip(arr, min_val, max_val)
