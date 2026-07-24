import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.schemas.common import BaseSchema
from src.utils.geometry import parse_polygonal_geojson, wkb_to_geojson


class RegionCreate(BaseModel):
    name: str = Field(..., max_length=255)
    geometry: dict[str, Any] = Field(..., description="GeoJSON polygon or multipolygon")

    @field_validator("geometry")
    @classmethod
    def validate_geometry(cls, value: dict[str, Any]) -> dict[str, Any]:
        parse_polygonal_geojson(value)
        return value


class RegionUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)


class RegionRead(BaseSchema):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    area_sq_km: float | None
    created_at: datetime
    updated_at: datetime

    geometry: dict[str, Any]

    @field_validator("geometry", mode="before")
    @classmethod
    def convert_geometry(cls, v: Any) -> dict[str, Any]:
        if isinstance(v, dict):
            return v
        # Assuming v is the WKBElement string from GeoAlchemy2
        return wkb_to_geojson(v)
