import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.db.models.user import User
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.enums import AuditResourceType
from src.db.models.mixins import BaseEntity, utc_now


class AuditLog(BaseEntity, Base):
    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resource_type: Mapped[AuditResourceType] = mapped_column(
        PgEnum(AuditResourceType, name="auditresourcetype_enum", create_type=False),
        nullable=False,
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="audit_logs", lazy="selectin"
    )
