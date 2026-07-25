from unittest.mock import MagicMock, patch

import pytest
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
from src.analytics.providers.cog_provider import COGRasterProvider
from src.analytics.types import BandIdentifier, PixelWindow


@pytest.fixture
def mock_dataset():
    mock_ds = MagicMock(spec=rasterio.DatasetReader)
    mock_ds.count = 3
    mock_ds.dtypes = ("uint16", "uint16", "uint16")
    mock_ds.nodatavals = (0, 0, 0)
    mock_ds.width = 100
    mock_ds.height = 100
    mock_ds.driver = "GTiff"
    mock_ds.meta = {"driver": "GTiff"}
    mock_ds.profile = {"compress": "deflate"}

    mock_crs = MagicMock()
    mock_crs.to_string.return_value = "EPSG:32610"
    mock_crs.__bool__.return_value = True  # acts as truthy
    mock_ds.crs = mock_crs

    mock_bounds = MagicMock()
    mock_bounds.left = -120.0
    mock_bounds.bottom = 30.0
    mock_bounds.right = -119.0
    mock_bounds.top = 31.0
    mock_ds.bounds = mock_bounds

    mock_ds.res = (10.0, 10.0)

    mock_transform = MagicMock()
    mock_transform.a = 10.0
    mock_transform.b = 0.0
    mock_transform.c = 500000.0
    mock_transform.d = 0.0
    mock_transform.e = -10.0
    mock_transform.f = 4000000.0
    mock_ds.transform = mock_transform

    mock_ds.read.return_value = b"fake_data"

    return mock_ds


@pytest.mark.asyncio
async def test_cog_provider_open_close(mock_dataset):
    with patch("rasterio.open", return_value=mock_dataset) as mock_open:
        provider = COGRasterProvider()
        await provider.open("dummy.tif")
        mock_open.assert_called_once_with("dummy.tif")
        assert provider.dataset is not None

        await provider.close()
        mock_dataset.close.assert_called_once()
        assert provider.dataset is None


@pytest.mark.asyncio
async def test_cog_provider_open_error():
    with patch("rasterio.open", side_effect=RasterioIOError("Not found")):
        provider = COGRasterProvider()
        with pytest.raises(RasterOpenError, match="Failed to open raster"):
            await provider.open("missing.tif")


@pytest.mark.asyncio
async def test_cog_provider_context_manager(mock_dataset):
    with patch("rasterio.open", return_value=mock_dataset):
        async with COGRasterProvider() as provider:
            assert isinstance(provider, COGRasterProvider)
            await provider.open("dummy.tif")
            assert provider.dataset is not None
        mock_dataset.close.assert_called_once()


@pytest.mark.asyncio
async def test_cog_provider_metadata(mock_dataset):
    with patch("rasterio.open", return_value=mock_dataset):
        async with COGRasterProvider() as provider:
            await provider.open("dummy.tif")
            meta = await provider.metadata()

            assert meta.crs == "EPSG:32610"
            assert meta.width == 100
            assert meta.height == 100
            assert len(meta.bands) == 3
            assert meta.driver == "GTiff"
            assert meta.compression == "deflate"


@pytest.mark.asyncio
async def test_cog_provider_read_not_open():
    provider = COGRasterProvider()
    with pytest.raises(RasterReadError, match="Raster is not open"):
        await provider.read_band(BandIdentifier("1"))


@pytest.mark.asyncio
async def test_cog_provider_read_band(mock_dataset):
    # Setup mock to return a mock numpy array with tobytes
    mock_arr = MagicMock()
    mock_arr.tobytes.return_value = b"band1"
    mock_dataset.read.return_value = mock_arr

    with patch("rasterio.open", return_value=mock_dataset):
        async with COGRasterProvider() as provider:
            await provider.open("dummy.tif")

            # Read full band
            data = await provider.read_band(BandIdentifier("1"))
            assert data == b"band1"
            mock_dataset.read.assert_called_with(1, window=None)

            # Read band with window
            win = PixelWindow(col_off=10, row_off=10, width=50, height=50)
            data2 = await provider.read_band(BandIdentifier("1"), window=win)
            assert data2 == b"band1"
            # Ensure window was passed to read
            args, kwargs = mock_dataset.read.call_args
            assert isinstance(kwargs["window"], Window)


@pytest.mark.asyncio
async def test_cog_provider_read_invalid_band(mock_dataset):
    with patch("rasterio.open", return_value=mock_dataset):
        async with COGRasterProvider() as provider:
            await provider.open("dummy.tif")
            with pytest.raises(InvalidBandError, match="out of range"):
                await provider.read_band(BandIdentifier("99"))

            with pytest.raises(InvalidBandError, match="must be an integer"):
                await provider.read_band(BandIdentifier("invalid"))


@pytest.mark.asyncio
async def test_cog_provider_read_window(mock_dataset):
    mock_arr = MagicMock()
    mock_arr.tobytes.return_value = b"window_data"
    mock_dataset.read.return_value = mock_arr

    with patch("rasterio.open", return_value=mock_dataset):
        async with COGRasterProvider() as provider:
            await provider.open("dummy.tif")
            win = PixelWindow(col_off=0, row_off=0, width=10, height=10)

            # Read all bands for window
            data = await provider.read_window(win)
            assert data == b"window_data"
            mock_dataset.read.assert_called_with(
                indexes=[1, 2, 3],
                window=Window(col_off=0, row_off=0, width=10, height=10),
            )

            # Read specific bands
            await provider.read_window(
                win, bands=[BandIdentifier("1"), BandIdentifier("3")]
            )
            mock_dataset.read.assert_called_with(
                indexes=[1, 3], window=Window(col_off=0, row_off=0, width=10, height=10)
            )


@pytest.mark.asyncio
async def test_cog_provider_validate(mock_dataset):
    with patch("rasterio.open", return_value=mock_dataset):
        async with COGRasterProvider() as provider:
            await provider.open("dummy.tif")
            assert await provider.validate() is True

            # Break driver
            mock_dataset.driver = None
            with pytest.raises(UnsupportedRasterError):
                await provider.validate()

            mock_dataset.driver = "GTiff"
            mock_dataset.count = 0
            with pytest.raises(RasterMetadataError, match="no bands"):
                await provider.validate()
