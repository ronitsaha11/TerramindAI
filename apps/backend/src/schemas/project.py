import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.db.models.enums import ProjectStatus
from src.schemas.common import BaseSchema


class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    status: ProjectStatus | None = None


class ProjectRead(BaseSchema):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
