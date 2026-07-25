import numpy as np


def is_all_nan(arr: np.ndarray) -> bool:
    """
    Check if an array contains entirely NaN values.
    Useful for short-circuiting expensive statistical calculations.
    """
    return bool(np.all(np.isnan(arr)))


def get_valid_mask(arr: np.ndarray) -> np.ndarray:
    """
    Returns a boolean mask of valid (non-NaN) pixels.
    """
    return ~np.isnan(arr)


def get_finite_mask(arr: np.ndarray) -> np.ndarray:
    """
    Returns a boolean mask of finite pixels.
    Excludes NaN, +inf, -inf.
    """
    return np.isfinite(arr)
