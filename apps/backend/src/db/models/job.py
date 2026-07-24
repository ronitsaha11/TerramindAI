import uuid
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, UUID

from src.db.models.base import Base
from src.db.models.mixins import BaseEntity, utc_now
from src.db.models.enums import JobType, JobStatus

class Job(BaseEntity, Base):
    __tablename__ = "jobs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("projects.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("regions.id", ondelete="CASCADE"), 
        nullable=True,
        index=True
    )
    
    job_type: Mapped[JobType] = mapped_column(
        PgEnum(JobType, name="jobtype_enum", create_type=False),
        nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        PgEnum(JobStatus, name="jobstatus_enum", create_type=False),
        default=JobStatus.QUEUED,
        nullable=False,
        index=True
    )
    
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    submitted_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="jobs")
    region: Mapped["Region"] = relationship("Region", back_populates="jobs")
    
    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction",
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
