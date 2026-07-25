from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.db.models.lineage_record import LineageRecord

from geoalchemy2 import Geometry
from sqlalchemy import ARRAY, JSON, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.mixins import BaseEntity


class SatelliteScene(BaseEntity, Base):
    __tablename__ = "satellite_scenes"

    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    scene_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    acquisition_date: Mapped[datetime] = mapped_column(nullable=False, index=True)
    cloud_cover: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Bounding box coordinates could be stored as JSON or a simpler text format.
    bbox: Mapped[list | None] = mapped_column(JSON, nullable=True)

    stac_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    cog_href: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    resolution: Mapped[float | None] = mapped_column(Float, nullable=True)

    # List of bands available (e.g., ["B02", "B03", "B04", "B08"])
    bands: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # Scene footprint globally in EPSG:4326 with GiST index
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), nullable=False
    )

    # Relationships
    lineage_records: Mapped[list["LineageRecord"]] = relationship(
        "LineageRecord", back_populates="scene"
    )
