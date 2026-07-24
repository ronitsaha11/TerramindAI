import uuid
from typing import List
from sqlalchemy import String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, UUID

from src.db.models.base import Base
from src.db.models.mixins import BaseEntity
from src.db.models.enums import ProjectStatus

class Project(BaseEntity, Base):
    __tablename__ = "projects"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="RESTRICT"), 
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        PgEnum(ProjectStatus, name="projectstatus_enum", create_type=False),
        default=ProjectStatus.ACTIVE,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_project_owner_name"),
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_projects", lazy="selectin")
    
    members: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember", 
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    regions: Mapped[List["Region"]] = relationship(
        "Region", 
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    
    jobs: Mapped[List["Job"]] = relationship(
        "Job", 
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
