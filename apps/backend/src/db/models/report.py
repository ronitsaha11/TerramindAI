import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, UUID

from src.db.models.base import Base
from src.db.models.mixins import BaseEntity, utc_now
from src.db.models.enums import ReportFormat

class Report(BaseEntity, Base):
    __tablename__ = "reports"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("projects.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    prediction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), 
        # Explicit SET NULL on delete for prediction->report
        ForeignKey("predictions.id", ondelete="SET NULL"), 
        nullable=True,
        index=True
    )
    
    format: Mapped[ReportFormat] = mapped_column(
        PgEnum(ReportFormat, name="reportformat_enum", create_type=False),
        nullable=False
    )
    
    storage_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    generated_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="reports")
    prediction: Mapped["Prediction"] = relationship("Prediction", back_populates="reports")
