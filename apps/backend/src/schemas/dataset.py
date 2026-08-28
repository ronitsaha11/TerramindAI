import uuid
from datetime import datetime

from pydantic import Field

from src.schemas.common import BaseSchema


class DatasetRead(BaseSchema):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    type: str
    geometry_type: str | None
    extent: list[float] | None = Field(
        None, description="Bounding box [minx, miny, maxx, maxy]"
    )
    crs: str
    feature_count: int
    attributes: dict | None = Field(
        None, description="Schema of attribute keys and types"
    )
    source: str | None
    created_at: datetime
    updated_at: datetime
