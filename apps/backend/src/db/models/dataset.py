import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.mixins import BaseEntity

if TYPE_CHECKING:
    from src.db.models.dataset_feature import DatasetFeature
    from src.db.models.project import Project


class Dataset(BaseEntity, Base):
    __tablename__ = "datasets"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="geojson")
    geometry_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Bounding box [minx, miny, maxx, maxy]; stored as a JSON array, which is
    # what DatasetRead.extent and the API response both expect.
    extent: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    crs: Mapped[str] = mapped_column(String(50), nullable=False, default="EPSG:4326")
    feature_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="datasets")
    features: Mapped[list["DatasetFeature"]] = relationship(
        "DatasetFeature",
        back_populates="dataset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
