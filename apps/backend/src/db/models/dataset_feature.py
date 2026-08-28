import uuid
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.mixins import BaseEntity

if TYPE_CHECKING:
    from src.db.models.dataset import Dataset


class DatasetFeature(BaseEntity, Base):
    __tablename__ = "dataset_features"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
        nullable=False,
    )
    properties: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="features")
