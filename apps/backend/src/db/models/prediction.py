import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.db.models.job import Job
    from src.db.models.lineage_record import LineageRecord
    from src.db.models.report import Report

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.enums import PredictionType
from src.db.models.mixins import BaseEntity


class Prediction(BaseEntity, Base):
    __tablename__ = "predictions"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    prediction_type: Mapped[PredictionType] = mapped_column(
        PgEnum(PredictionType, name="predictiontype_enum", create_type=False),
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    artifact_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="predictions")

    lineage_records: Mapped[list["LineageRecord"]] = relationship(
        "LineageRecord",
        back_populates="prediction",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="prediction",
        # Explicit SET NULL on delete for prediction->report
        cascade="save-update, merge",
    )
