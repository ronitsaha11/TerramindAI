from src.analytics.indices.base import SpectralIndex
from src.analytics.indices.engine import IndexEngine
from src.analytics.indices.ndvi import NDVIIndex
from src.analytics.indices.ndwi import NDWIIndex
from src.analytics.indices.registry import IndexRegistry
from src.analytics.indices.utils import clip_output, mask_invalid_pixels, safe_divide

# Pre-configured global registry
default_registry = IndexRegistry()
default_registry.register(NDVIIndex())
default_registry.register(NDWIIndex())

# Pre-configured global engine
default_engine = IndexEngine(default_registry)


__all__ = [
    "SpectralIndex",
    "IndexRegistry",
    "IndexEngine",
    "NDVIIndex",
    "NDWIIndex",
    "safe_divide",
    "mask_invalid_pixels",
    "clip_output",
    "default_registry",
    "default_engine",
]
