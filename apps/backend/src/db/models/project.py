import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.enums import ProjectStatus
from src.db.models.mixins import BaseEntity

if TYPE_CHECKING:
    from src.db.models.job import Job
    from src.db.models.project_member import ProjectMember
    from src.db.models.region import Region
    from src.db.models.report import Report
    from src.db.models.user import User


class Project(BaseEntity, Base):
    __tablename__ = "projects"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        PgEnum(ProjectStatus, name="projectstatus_enum", create_type=False),
        default=ProjectStatus.ACTIVE,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_project_owner_name"),
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User", back_populates="owned_projects", lazy="selectin"
    )

    members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    regions: Mapped[list["Region"]] = relationship(
        "Region",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    jobs: Mapped[list["Job"]] = relationship(
        "Job",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
