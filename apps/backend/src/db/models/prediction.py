import uuid
from datetime import datetime
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, UUID

from src.db.models.base import Base
from src.db.models.mixins import BaseEntity, utc_now
from src.db.models.enums import PredictionType

class Prediction(BaseEntity, Base):
    __tablename__ = "predictions"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("jobs.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    prediction_type: Mapped[PredictionType] = mapped_column(
        PgEnum(PredictionType, name="predictiontype_enum", create_type=False),
        nullable=False
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
        passive_deletes=True
    )
    
    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="prediction",
        # Explicit SET NULL on delete for prediction->report
        cascade="save-update, merge" 
    )
