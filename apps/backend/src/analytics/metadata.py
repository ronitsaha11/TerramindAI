"""
Implementations for MetadataExtractor.

Responsible for parsing STAC items, GeoTIFF tags, and external API
metadata dictionaries into strongly typed RasterMetadata domain models.
"""

from src.analytics.providers import MetadataExtractor


class DefaultMetadataExtractor(MetadataExtractor):
    """
    Placeholder for default metadata extractor.
    Will parse standard STAC responses and GeoTIFF tags in future milestones.
    """

    pass
