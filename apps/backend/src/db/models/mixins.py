import uuid
from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class BaseEntity:
    """
    Reusable mixin providing UUID primary key, standard audit timestamps, 
    and soft-delete support for all domain models.
    """
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    
    created_at: Mapped[datetime] = mapped_column(
        default=utc_now, 
        server_default=func.now()
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        default=utc_now, 
        server_default=func.now(), 
        onupdate=utc_now
    )
    
    deleted_at: Mapped[datetime | None] = mapped_column(
        default=None, 
        nullable=True
    )
