from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class STACSearchQuery(BaseModel):
    collections: list[str] = Field(min_length=1)
    bbox: list[float] = Field(min_length=4, max_length=4)
    datetime: str | None = None
    limit: int = Field(default=20, ge=1, le=100)

    @field_validator("bbox")
    @classmethod
    def validate_bbox_coordinates(cls, value: list[float]) -> list[float]:
        west, south, east, north = value
        if not (-180 <= west <= 180 and -180 <= east <= 180):
            raise ValueError("bbox longitude values must be between -180 and 180")
        if not (-90 <= south <= 90 and -90 <= north <= 90):
            raise ValueError("bbox latitude values must be between -90 and 90")
        return value

    @model_validator(mode="after")
    def validate_bbox_order(self) -> "STACSearchQuery":
        west, south, east, north = self.bbox
        if west >= east or south >= north:
            raise ValueError("bbox must be ordered as west, south, east, north")
        return self

    @field_validator("datetime")
    @classmethod
    def validate_datetime_interval(cls, value: str | None) -> str | None:
        if value is None:
            return value
        values = value.split("/")
        if len(values) > 2 or not values:
            raise ValueError("datetime must be an ISO 8601 instant or interval")
        try:
            for part in values:
                if part != "..":
                    datetime.fromisoformat(part.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(
                "datetime must be an ISO 8601 instant or interval"
            ) from exc
        return value


class SatelliteSceneRead(BaseModel):
    id: str
    collection: str
    acquired_at: datetime
    bbox: list[float]
    cloud_cover: float | None = None
    # STAC asset href – an arbitrary URI reference (https://, s3://, gs://, etc.).
    # Transport-scheme validation belongs in TileService, not the provider layer.
    cog_href: str | None = None


class TileMetadata(BaseModel):
    bounds: list[float] | None = None
    minzoom: int | None = None
    maxzoom: int | None = None


class TileTemplateResponse(BaseModel):
    # XYZ placeholders such as {z}/{x}/{y} are not valid strict URLs.
    tiles: list[str] = Field(min_length=1)
    minzoom: int | None = None
    maxzoom: int | None = None
