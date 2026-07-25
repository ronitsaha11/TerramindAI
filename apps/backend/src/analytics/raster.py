"""
Implementations for RasterProvider.

Currently defines only abstract placeholders and future integration points
for concrete raster engines (e.g. Rasterio-based COG provider).
"""

from src.analytics.providers.base import RasterProvider


class COGRasterProvider(RasterProvider):
    """
    Will implement the RasterProvider ABC using rasterio or
    similar in future milestones.
    """

    pass
