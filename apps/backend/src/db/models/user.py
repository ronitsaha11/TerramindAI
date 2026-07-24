from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.db.models.audit_log import AuditLog
    from src.db.models.project import Project
    from src.db.models.project_member import ProjectMember
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.mixins import BaseEntity


class User(BaseEntity, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="user")

    # Relationships
    owned_projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
        # RESTRICT logic is typically handled by the DB constraint,
        # but SQLAlchemy doesn't have a direct 'RESTRICT'
        # cascade string for Python side.
        # We will configure the ForeignKey in Project to handle ondelete="RESTRICT".
    )

    project_memberships: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )
