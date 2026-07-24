import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from src.db.models.base import Base
from src.db.models.mixins import BaseEntity, utc_now

class LineageRecord(BaseEntity, Base):
    __tablename__ = "lineage_records"

    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("predictions.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("satellite_scenes.id", ondelete="RESTRICT"), 
        nullable=False,
        index=True
    )
    
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    preprocessing: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    git_commit_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    software_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    tile_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    crs: Mapped[str | None] = mapped_column(String(20), nullable=True)
    inference_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    generated_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)

    # Relationships
    prediction: Mapped["Prediction"] = relationship("Prediction", back_populates="lineage_records")
    scene: Mapped["SatelliteScene"] = relationship("SatelliteScene", back_populates="lineage_records")
