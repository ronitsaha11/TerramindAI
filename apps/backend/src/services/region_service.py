import uuid
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError

from src.core.exceptions import AppException
from src.db.models.region import Region
from src.schemas.region import RegionCreate, RegionRead
from src.services.conflicts import is_unique_violation
from src.unit_of_work import UnitOfWork
from src.utils.geometry import calculate_area_sq_km, geojson_to_wkt


class RegionService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_region(
        self, project_id: uuid.UUID, data: RegionCreate
    ) -> RegionRead:
        try:
            async with self.uow:
                project = await self.uow.projects.get_by_id(project_id)
                if not project:
                    raise AppException(status_code=404, detail="Project not found.")

                wkt_geometry = geojson_to_wkt(data.geometry)
                area_sq_km = calculate_area_sq_km(data.geometry)

                region = Region(
                    project_id=project_id,
                    name=data.name,
                    geometry=f"SRID=4326;{wkt_geometry}",  # GeoAlchemy2 expects SRID
                    area_sq_km=area_sq_km,
                )

                await self.uow.regions.create(region)
                await self.uow.commit()

                return RegionRead.model_validate(region)
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise AppException(
                    status_code=409,
                    detail="Region name already exists in this project.",
                ) from exc
            raise

    async def list_regions(self, project_id: uuid.UUID) -> Sequence[RegionRead]:
        async with self.uow:
            project = await self.uow.projects.get_by_id(project_id)
            if not project:
                raise AppException(status_code=404, detail="Project not found.")

            regions = await self.uow.regions.find_by_project(project_id)
            return [RegionRead.model_validate(r) for r in regions]
