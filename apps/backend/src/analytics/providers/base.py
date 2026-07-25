import abc
from collections.abc import Sequence

from src.analytics.models import BandInfo, RasterMetadata
from src.analytics.types import (
    BandIdentifier,
    BoundingBox,
    CoordinateReferenceSystem,
    PixelWindow,
    RasterResolution,
)


class RasterProvider(abc.ABC):
    """
    Abstract interface for interacting with geospatial rasters.
    Implementations may support COG, local GeoTIFF, Sentinel Hub, etc.
    """

    @abc.abstractmethod
    async def open(self, uri: str) -> None:
        """Open the raster connection."""
        pass

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the raster connection and free resources."""
        pass

    async def __aenter__(self) -> "RasterProvider":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    @abc.abstractmethod
    async def metadata(self) -> RasterMetadata:
        """Fetch the full raster metadata."""
        pass

    @abc.abstractmethod
    async def crs(self) -> CoordinateReferenceSystem:
        """Get the coordinate reference system."""
        pass

    @abc.abstractmethod
    async def bounds(self) -> BoundingBox:
        """Get the geospatial bounding box."""
        pass

    @abc.abstractmethod
    async def resolution(self) -> RasterResolution:
        """Get the spatial resolution."""
        pass

    @abc.abstractmethod
    async def shape(self) -> tuple[int, int]:
        """Get the raster shape as (height, width)."""
        pass

    @abc.abstractmethod
    async def validate(self) -> bool:
        """Validate that the raster is healthy and supported."""
        pass

    @abc.abstractmethod
    async def available_bands(self) -> Sequence[BandInfo]:
        """List all available bands in the raster."""
        pass

    @abc.abstractmethod
    async def read_window(
        self, window: PixelWindow, bands: Sequence[BandIdentifier] | None = None
    ) -> bytes:
        """Read a raw pixel window from the raster for the specified bands."""
        pass

    @abc.abstractmethod
    async def read_band(
        self, band: BandIdentifier, window: PixelWindow | None = None
    ) -> bytes:
        """Read a single band's data, optionally constrained by a window."""
        pass


class StatisticsProvider(abc.ABC):
    """
    Abstract interface for computing statistics over raster arrays.
    """

    @abc.abstractmethod
    def compute(self, data: bytes, nodata: float | None = None) -> dict[str, float]:
        """
        Compute basic statistics (min, max, mean, std) over the given data array.
        """
        pass


class MetadataExtractor(abc.ABC):
    """
    Abstract interface for extracting specialized metadata.
    """

    @abc.abstractmethod
    def extract(self, raw_metadata: dict) -> RasterMetadata:
        """
        Map a provider-specific metadata dictionary into the domain RasterMetadata.
        """
        pass
