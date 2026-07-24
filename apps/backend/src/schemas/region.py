import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.schemas.common import BaseSchema
from src.utils.geometry import wkb_to_geojson


class RegionCreate(BaseModel):
    name: str = Field(..., max_length=255)
    geometry: dict = Field(..., description="GeoJSON polygon or multipolygon")


class RegionUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)


class RegionRead(BaseSchema):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    area_sq_km: float | None
    created_at: datetime
    updated_at: datetime

    geometry: dict

    @field_validator("geometry", mode="before")
    @classmethod
    def convert_geometry(cls, v: Any) -> dict:
        if isinstance(v, dict):
            return v
        # Assuming v is the WKBElement string from GeoAlchemy2
        return wkb_to_geojson(v)
