import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.db.models.job import Job
    from src.db.models.project import Project

from geoalchemy2 import Geometry
from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.mixins import BaseEntity


class Region(BaseEntity, Base):
    __tablename__ = "regions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Store globally in EPSG:4326.
    # GiST index is created automatically by geoalchemy2 if spatial_index=True.
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True),
        nullable=False,
    )

    area_sq_km: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_region_project_name"),
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="regions")

    jobs: Mapped[list["Job"]] = relationship(
        "Job",
        back_populates="region",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
