from typing import Any

import shapely.wkb
from geoalchemy2.elements import WKBElement
from shapely.geometry import MultiPolygon, mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.wkt import dumps

from src.core.exceptions import AppException


def parse_polygonal_geojson(geojson: dict[str, Any]) -> BaseGeometry:
    """Parse and validate a non-empty, valid GeoJSON Polygon or MultiPolygon."""
    try:
        geom = shape(geojson)
    except Exception as exc:
        raise ValueError("geometry must be a valid GeoJSON geometry") from exc

    if geom.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError("geometry must be a GeoJSON Polygon or MultiPolygon")
    if geom.is_empty:
        raise ValueError("geometry must not be empty")
    if not geom.is_valid:
        raise ValueError("geometry must be valid and must not self-intersect")

    return geom


def geojson_to_wkt(geojson: dict[str, Any]) -> str:
    """Converts a GeoJSON geometry dictionary to a WKT string for PostGIS."""
    try:
        geom = parse_polygonal_geojson(geojson)
        # The database column is MULTIPOLYGON, so normalize accepted Polygons.
        if geom.geom_type == "Polygon":
            geom = MultiPolygon([geom])
        return dumps(geom)
    except ValueError as exc:
        raise AppException(
            status_code=400, detail=f"Invalid GeoJSON geometry: {exc}"
        ) from exc


def wkb_to_geojson(wkb_element: WKBElement | str) -> dict[str, Any]:
    """
    Converts a GeoAlchemy2 WKBElement or hex string to a GeoJSON
    geometry dictionary.
    """
    try:
        if isinstance(wkb_element, WKBElement):
            data = wkb_element.data
            if isinstance(data, str):
                geom = shapely.wkb.loads(bytes.fromhex(data))
            else:
                geom = shapely.wkb.loads(data)
        elif isinstance(wkb_element, str):
            geom = shapely.wkb.loads(bytes.fromhex(wkb_element))
        else:
            geom = shapely.wkb.loads(wkb_element)

        return dict(mapping(geom))
    except Exception as e:
        raise AppException(
            status_code=500, detail=f"Failed to parse geometry from database: {str(e)}"
        ) from e


def calculate_area_sq_km(geojson: dict[str, Any]) -> float:
    """
    Approximates the area of a GeoJSON geometry in square kilometers.
    In a real system, use pyproj to transform EPSG:4326 to an equal-area projection.
    """
    try:
        geom = shape(geojson)
        # Rough approximation for demonstration: 1 sq degree ~ 12365.16 sq km
        return float(geom.area * 12365.16)
    except Exception:
        return 0.0
