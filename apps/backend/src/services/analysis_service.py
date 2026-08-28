"""
Analysis Service — orchestration layer for the Earth Intelligence Engine.

This service coordinates all analytics components into a single, reliable
analysis pipeline. It performs NO mathematical calculations — those are
delegated to the Spectral Index Engine and Statistics Engine respectively.
"""

import math
from datetime import UTC, datetime
from uuid import uuid4

import numpy as np

from src.analytics.enums import ProcessingStatus
from src.analytics.exceptions import (
    AnalysisValidationError,
    ProviderError,
    RasterOpenError,
    StatisticsError,
)
from src.analytics.indices.engine import IndexEngine
from src.analytics.indices.registry import IndexRegistry
from src.analytics.models import AnalysisRequest, AnalysisResult, RasterMetadata
from src.analytics.providers.base import RasterProvider
from src.analytics.statistics.engine import StatisticsEngine
from src.analytics.statistics.schemas import StatisticsSummary
from src.analytics.types import BandIdentifier, PixelWindow


class AnalysisService:
    """
    Orchestrates the complete Earth Intelligence pipeline.

    Workflow:
        1. Validate the incoming AnalysisRequest
        2. Open the raster via the injected RasterProvider (async context manager)
        3. Read only the required bands for the requested index
        4. Resolve and compute the spectral index
        5. Compute statistics on the resulting index array
        6. Construct and return a complete AnalysisResult

    This service must remain usable from REST handlers, Celery workers,
    CLI tools, and scheduled jobs without modification.
    """

    def __init__(
        self,
        raster_provider: RasterProvider,
        index_registry: IndexRegistry,
        statistics_engine: StatisticsEngine,
    ) -> None:
        self._raster_provider = raster_provider
        self._index_registry = index_registry
        self._statistics_engine = statistics_engine
        self._index_engine = IndexEngine(index_registry)

    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Execute the full analysis pipeline for the given request.

        Args:
            request: Validated AnalysisRequest domain model.

        Returns:
            AnalysisResult with processing status, metadata, and statistics.
        """
        analysis_id = uuid4()
        started_at = datetime.now(UTC)

        # Step 1 – Validate the request
        self._validate_request(request)

        # Resolve spectral index early to fail fast before touching raster I/O
        index_name = request.requested_analysis.upper()
        index = self._index_registry.get(index_name)

        # Step 2–5 – Open raster, read, compute — guaranteed cleanup via context
        try:
            async with self._raster_provider as provider:
                # Step 2: Open raster resource
                try:
                    await provider.open(request.scene_id)
                except Exception as exc:
                    raise RasterOpenError(
                        f"Could not open scene '{request.scene_id}': {exc}"
                    ) from exc

                # Step 3: Extract raster metadata
                raster_metadata = await provider.metadata()

                # Step 4: Determine which bands to read
                bands_to_read = self._resolve_bands(
                    index.required_bands,
                    raster_metadata,
                )

                # Step 5: Read the required bands as raw NumPy arrays
                window = self._resolve_window(request, raster_metadata)
                band_arrays = await self._read_bands(provider, bands_to_read, window)

                # Step 6: Compute the spectral index
                try:
                    index_array: np.ndarray = self._index_engine.compute(
                        index_name, band_arrays
                    )
                except AnalysisValidationError:
                    raise
                except Exception as exc:
                    raise AnalysisValidationError(
                        f"Spectral index computation failed: {exc}"
                    ) from exc

                # Step 7: Compute statistics
                try:
                    statistics: StatisticsSummary = (
                        self._statistics_engine.compute_statistics(index_array)
                    )
                except Exception as exc:
                    raise StatisticsError(
                        f"Statistics computation failed: {exc}"
                    ) from exc

        except (RasterOpenError, AnalysisValidationError, StatisticsError):
            raise
        except Exception as exc:
            raise ProviderError(
                f"Unexpected provider error during analysis: {exc}"
            ) from exc

        # Step 8: Construct the complete AnalysisResult
        return AnalysisResult(
            analysis_id=analysis_id,
            request=request,
            processing_status=ProcessingStatus.COMPLETED,
            created_at=started_at,
            completed_at=datetime.now(UTC),
            raster_metadata=raster_metadata,
            statistics=statistics,
        )

    def _validate_request(self, request: AnalysisRequest) -> None:
        """Perform domain-level validation on the incoming request."""
        if not request.scene_id.strip():
            raise AnalysisValidationError("scene_id must not be empty")

        # Ensure the requested analysis maps to a registered index
        try:
            self._index_registry.get(request.requested_analysis.upper())
        except AnalysisValidationError as exc:
            raise AnalysisValidationError(
                f"Unsupported analysis type '{request.requested_analysis}': {exc}"
            ) from exc

    def _resolve_bands(
        self,
        required_band_names: list[str],
        metadata: RasterMetadata,
    ) -> list[tuple[str, BandIdentifier]]:
        """
        Map index band names (e.g. 'NIR', 'RED') to actual raster band indices.
        Returns a list of (semantic_name, band_id) pairs so the index engine
        receives semantic keys and the provider receives numeric identifiers.
        """
        available_count = len(metadata.bands)

        # Prefer the raster's own band labels. Mapping purely by position means
        # a raster whose bands are ordered differently to the requested index
        # returns confident but meaningless values, with no error - NDVI and
        # NDWI are both (b1 - b2)/(b1 + b2), so nothing downstream can detect it.
        labelled: dict[str, BandIdentifier] = {}
        for band in metadata.bands:
            for label in (band.name, band.common_name, band.description):
                if label:
                    labelled.setdefault(label.strip().upper(), band.identifier)

        if labelled:
            missing = [n for n in required_band_names if n.upper() not in labelled]
            if missing:
                raise AnalysisValidationError(
                    f"Raster labels its bands {sorted(labelled)}, which does not "
                    f"provide {missing} required by this index. Refusing to fall "
                    f"back to positional order, which would read the wrong bands "
                    f"and return plausible but incorrect values."
                )
            return [(n, labelled[n.upper()]) for n in required_band_names]

        # Unlabelled raster: positional mapping is the only option available.
        mapping: list[tuple[str, BandIdentifier]] = []
        for i, name in enumerate(required_band_names, start=1):
            if i > available_count:
                raise AnalysisValidationError(
                    f"Raster has {available_count} band(s) but index requires "
                    f"band '{name}' (position {i})"
                )
            mapping.append((name, BandIdentifier(str(i))))

        return mapping

    def _resolve_window(
        self,
        request: AnalysisRequest,
        metadata: RasterMetadata,
    ) -> PixelWindow | None:
        """
        Convert an area-of-interest BoundingBox into a PixelWindow.
        Returns None for full-raster reads.

        Previously this returned None unconditionally, so an area_of_interest
        was accepted, validated and then silently discarded - callers received
        whole-raster statistics with no indication their AOI was ignored.
        Unsupported cases now raise instead of quietly widening the read.
        """
        aoi = request.area_of_interest
        if aoi is None:
            return None

        t = metadata.transform

        if t.b or t.d:
            raise AnalysisValidationError(
                "area_of_interest is not supported for rotated or sheared "
                "rasters; the affine transform has non-zero rotation terms."
            )
        if not t.a or not t.e:
            raise AnalysisValidationError(
                "Raster transform reports zero pixel size; cannot resolve "
                "area_of_interest."
            )

        crs = (metadata.crs or "").strip().upper()
        if crs not in {"EPSG:4326", "OGC:CRS84", "CRS84"}:
            raise AnalysisValidationError(
                f"area_of_interest is expressed in lon/lat but the raster CRS "
                f"is '{metadata.crs}'. Reprojecting the AOI is not supported "
                f"yet, and applying it unprojected would select the wrong pixels."
            )

        # Inverse of a north-up affine: col = (x - c)/a, row = (y - f)/e.
        cols = sorted(((aoi.west - t.c) / t.a, (aoi.east - t.c) / t.a))
        rows = sorted(((aoi.north - t.f) / t.e, (aoi.south - t.f) / t.e))

        col_off = max(0, math.floor(cols[0]))
        row_off = max(0, math.floor(rows[0]))
        col_end = min(metadata.width, math.ceil(cols[1]))
        row_end = min(metadata.height, math.ceil(rows[1]))

        if col_end <= col_off or row_end <= row_off:
            raise AnalysisValidationError(
                "area_of_interest does not intersect the raster extent."
            )

        return PixelWindow(
            col_off=col_off,
            row_off=row_off,
            width=col_end - col_off,
            height=row_end - row_off,
        )

    async def _read_bands(
        self,
        provider: RasterProvider,
        band_mapping: list[tuple[str, BandIdentifier]],
        window: PixelWindow | None,
    ) -> dict[str, np.ndarray]:
        """
        Read each required band and return a mapping of semantic name to NumPy array.
        The provider reads by numeric band ID; the result is keyed by semantic name
        (e.g. 'NIR') so the index engine can consume it directly.
        """
        result: dict[str, np.ndarray] = {}

        for semantic_name, band_id in band_mapping:
            raw: bytes = await provider.read_band(band_id, window=window)
            # Reconstruct float32 array from raw bytes written by provider.tobytes()
            arr = np.frombuffer(raw, dtype=np.float32)
            result[semantic_name] = arr

        return result
