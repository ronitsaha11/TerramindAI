import asyncio
from collections.abc import Sequence

import rasterio
from rasterio.errors import RasterioIOError
from rasterio.windows import Window

from src.analytics.exceptions import (
    InvalidBandError,
    RasterMetadataError,
    RasterOpenError,
    RasterReadError,
    UnsupportedRasterError,
)
from src.analytics.models import BandInfo, RasterMetadata
from src.analytics.providers.base import RasterProvider
from src.analytics.types import (
    BandIdentifier,
    BoundingBox,
    CoordinateReferenceSystem,
    GeoTransform,
    PixelWindow,
    RasterResolution,
)


class COGRasterProvider(RasterProvider):
    """
    Concrete implementation of RasterProvider utilizing rasterio to read
    Cloud Optimized GeoTIFFs (COGs) and other GDAL-compatible rasters.
    """

    def __init__(self) -> None:
        self.uri: str | None = None
        self.dataset: rasterio.DatasetReader | None = None

    async def open(self, uri: str) -> None:
        self.uri = uri
        try:
            self.dataset = await asyncio.to_thread(rasterio.open, uri)
        except RasterioIOError as e:
            raise RasterOpenError(f"Failed to open raster {uri}: {str(e)}") from e
        except Exception as e:
            raise RasterOpenError(f"Unexpected error opening {uri}: {str(e)}") from e

    def _ensure_open(self) -> rasterio.DatasetReader:
        if self.dataset is None:
            raise RasterReadError("Raster is not open")
        return self.dataset

    async def close(self) -> None:
        if self.dataset is not None:
            await asyncio.to_thread(self.dataset.close)
            self.dataset = None

    async def metadata(self) -> RasterMetadata:
        ds = self._ensure_open()
        try:
            # We run simple property access synchronously as it's cached in memory
            # after open.
            meta = ds.meta
            bounds = ds.bounds
            res = ds.res

            if not ds.crs:
                raise RasterMetadataError("Raster is missing CRS information")

            bands = []
            for i in range(1, ds.count + 1):
                bands.append(
                    BandInfo(
                        identifier=BandIdentifier(str(i)),
                        dtype=str(ds.dtypes[i - 1]),
                        nodata_value=ds.nodatavals[i - 1] if ds.nodatavals else None,
                    )
                )

            return RasterMetadata(
                crs=CoordinateReferenceSystem(ds.crs.to_string()),
                bounds=BoundingBox(
                    west=bounds.left,
                    south=bounds.bottom,
                    east=bounds.right,
                    north=bounds.top,
                ),
                resolution=RasterResolution(x=res[0], y=res[1]),
                transform=GeoTransform(
                    a=ds.transform.a,
                    b=ds.transform.b,
                    c=ds.transform.c,
                    d=ds.transform.d,
                    e=ds.transform.e,
                    f=ds.transform.f,
                ),
                bands=bands,
                width=ds.width,
                height=ds.height,
                driver=meta.get("driver"),
                compression=ds.profile.get("compress"),
            )
        except RasterMetadataError:
            raise
        except Exception as e:
            raise RasterMetadataError(f"Failed to parse metadata: {str(e)}") from e

    async def crs(self) -> CoordinateReferenceSystem:
        ds = self._ensure_open()
        if not ds.crs:
            raise RasterMetadataError("Missing CRS")
        return CoordinateReferenceSystem(ds.crs.to_string())

    async def bounds(self) -> BoundingBox:
        ds = self._ensure_open()
        b = ds.bounds
        return BoundingBox(west=b.left, south=b.bottom, east=b.right, north=b.top)

    async def resolution(self) -> RasterResolution:
        ds = self._ensure_open()
        res = ds.res
        return RasterResolution(x=res[0], y=res[1])

    async def shape(self) -> tuple[int, int]:
        ds = self._ensure_open()
        return ds.height, ds.width

    async def validate(self) -> bool:
        ds = self._ensure_open()
        if not ds.driver:
            raise UnsupportedRasterError("Raster has no defined driver")
        if ds.count < 1:
            raise RasterMetadataError("Raster has no bands")
        if not ds.crs:
            raise RasterMetadataError("Raster is missing CRS information")
        if ds.width <= 0 or ds.height <= 0:
            raise RasterMetadataError("Raster dimensions must be strictly positive")
        return True

    async def available_bands(self) -> Sequence[BandInfo]:
        md = await self.metadata()
        return md.bands

    def _read_window_sync(self, window: Window, indexes: list[int] | int) -> bytes:
        ds = self._ensure_open()
        try:
            arr = ds.read(indexes=indexes, window=window)
            return arr.tobytes()
        except Exception as e:
            raise RasterReadError(f"Failed to read window: {str(e)}") from e

    async def read_window(
        self, window: PixelWindow, bands: Sequence[BandIdentifier] | None = None
    ) -> bytes:
        ds = self._ensure_open()
        indexes: list[int] | int
        if bands is None:
            indexes = list(range(1, ds.count + 1))
        else:
            try:
                indexes = [int(b) for b in bands]
            except ValueError as e:
                raise InvalidBandError(
                    "Band identifiers must be integer indices for COG"
                ) from e
            for idx in indexes:
                if idx < 1 or idx > ds.count:
                    raise InvalidBandError(f"Band {idx} out of range")

        rio_window = Window(
            col_off=window.col_off,
            row_off=window.row_off,
            width=window.width,
            height=window.height,
        )

        return await asyncio.to_thread(self._read_window_sync, rio_window, indexes)

    def _read_band_sync(self, index: int, window: Window | None) -> bytes:
        ds = self._ensure_open()
        try:
            arr = ds.read(index, window=window)
            return arr.tobytes()
        except Exception as e:
            raise RasterReadError(f"Failed to read band: {str(e)}") from e

    async def read_band(
        self, band: BandIdentifier, window: PixelWindow | None = None
    ) -> bytes:
        ds = self._ensure_open()
        try:
            idx = int(band)
        except ValueError as e:
            raise InvalidBandError(
                "Band identifier must be an integer index for COG"
            ) from e

        if idx < 1 or idx > ds.count:
            raise InvalidBandError(f"Band {idx} out of range")

        rio_window = None
        if window is not None:
            rio_window = Window(
                col_off=window.col_off,
                row_off=window.row_off,
                width=window.width,
                height=window.height,
            )

        return await asyncio.to_thread(self._read_band_sync, idx, rio_window)
