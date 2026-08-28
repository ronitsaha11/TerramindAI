import json
import logging
import uuid
from collections.abc import Sequence

from shapely.geometry import shape

from src.core.exceptions import AppException
from src.db.models.dataset import Dataset
from src.schemas.dataset import DatasetRead
from src.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class DatasetService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_dataset_from_geojson(
        self,
        project_id: uuid.UUID,
        filename: str,
        geojson_content: bytes,
    ) -> DatasetRead:
        """Parse GeoJSON, compute metadata, and persist dataset + features."""
        try:
            data = json.loads(geojson_content)
        except json.JSONDecodeError as e:
            raise AppException(status_code=400, detail=f"Invalid JSON: {e}") from e

        if data.get("type") != "FeatureCollection":
            raise AppException(
                status_code=400,
                detail="Only GeoJSON FeatureCollections are supported.",
            )

        features_data = data.get("features", [])
        if not features_data:
            raise AppException(
                status_code=400, detail="FeatureCollection has no features."
            )

        # Compute metadata from real data
        geometry_types: set[str] = set()
        attribute_types: dict[str, str] = {}
        min_x, min_y, max_x, max_y = (
            float("inf"),
            float("inf"),
            float("-inf"),
            float("-inf"),
        )

        db_features: list[dict] = []

        async with self.uow:
            # Verify the project actually exists
            project = await self.uow.projects.get_by_id(project_id)
            if not project:
                raise AppException(status_code=404, detail="Project not found.")

            dataset_id = uuid.uuid4()
            dataset = Dataset(
                id=dataset_id,
                project_id=project_id,
                name=_derive_name(filename),
                type="geojson",
                crs="EPSG:4326",
                source=filename,
            )
            # Create it immediately to get an ID and allow relations
            await self.uow.datasets.create(dataset)

            for feat in features_data:
                geom_data = feat.get("geometry")
                props = feat.get("properties") or {}

                if not geom_data:
                    continue

                try:
                    geom = shape(geom_data)
                except Exception:
                    continue  # skip malformed geometries

                geometry_types.add(geom.geom_type)

                bounds = geom.bounds  # (minx, miny, maxx, maxy)
                min_x = min(min_x, bounds[0])
                min_y = min(min_y, bounds[1])
                max_x = max(max_x, bounds[2])
                max_y = max(max_y, bounds[3])

                # Track attribute types
                for key, value in props.items():
                    python_type = type(value).__name__
                    if key not in attribute_types:
                        attribute_types[key] = python_type

                db_features.append(
                    {
                        "dataset_id": dataset_id,
                        "geometry": f"SRID=4326;{geom.wkt}",
                        "properties": json.dumps(props),
                    }
                )

            if not db_features:
                raise AppException(
                    status_code=400, detail="No valid features found in file."
                )

            # Determine geometry type label
            # Determine geometry type label
            if len(geometry_types) == 1:
                geom_type = next(iter(geometry_types))
            else:
                geom_type = "Mixed"

            dataset.geometry_type = geom_type
            dataset.extent = [min_x, min_y, max_x, max_y]
            dataset.feature_count = len(db_features)
            dataset.attributes = attribute_types

            # Save dataset first
            await self.uow.datasets.create(dataset)

            # Explicitly insert features using the generated dataset_id
            await self.uow.dataset_features.bulk_create(db_features)

            await self.uow.commit()

            return DatasetRead.model_validate(dataset)

    async def list_datasets(self, project_id: uuid.UUID) -> Sequence[DatasetRead]:
        async with self.uow:
            project = await self.uow.projects.get_by_id(project_id)
            if not project:
                raise AppException(status_code=404, detail="Project not found.")
            datasets = await self.uow.datasets.find_by_project(project_id)
            return [DatasetRead.model_validate(d) for d in datasets]

    async def get_dataset_geojson(
        self, project_id: uuid.UUID, dataset_id: uuid.UUID
    ) -> dict:
        async with self.uow:
            dataset = await self.uow.datasets.get_by_id(dataset_id)
            if not dataset or dataset.project_id != project_id:
                raise AppException(status_code=404, detail="Dataset not found.")

            features = await self.uow.dataset_features.get_geojson_features(dataset_id)

            return {"type": "FeatureCollection", "features": features}

    async def query_nearby(
        self,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        lon: float,
        lat: float,
        radius_meters: float,
    ) -> dict:
        """Return features within *radius_meters* of the point (lon, lat)."""
        async with self.uow:
            dataset = await self.uow.datasets.get_by_id(dataset_id)
            if not dataset or dataset.project_id != project_id:
                raise AppException(status_code=404, detail="Dataset not found.")

            features = await self.uow.dataset_features.get_nearby_features(
                dataset_id=dataset_id,
                lon=lon,
                lat=lat,
                radius_meters=radius_meters,
            )

            return {
                "type": "FeatureCollection",
                "features": features,
            }

    async def query_contains(
        self,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        feature_id: uuid.UUID,
    ) -> dict:
        """Return features contained within the specified polygon feature."""
        async with self.uow:
            dataset = await self.uow.datasets.get_by_id(dataset_id)
            if not dataset or dataset.project_id != project_id:
                raise AppException(status_code=404, detail="Dataset not found.")

            features = await self.uow.dataset_features.get_contained_features(
                dataset_id=dataset_id,
                polygon_feature_id=feature_id,
            )

            return {
                "type": "FeatureCollection",
                "features": features,
            }

    async def query_intersects(
        self,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        feature_id: uuid.UUID,
        target_dataset_id: uuid.UUID,
    ) -> dict:
        """Return features of the target dataset intersecting the given feature."""
        async with self.uow:
            dataset = await self.uow.datasets.get_by_id(dataset_id)
            if not dataset or dataset.project_id != project_id:
                raise AppException(status_code=404, detail="Dataset not found.")

            target = await self.uow.datasets.get_by_id(target_dataset_id)
            if not target or target.project_id != project_id:
                raise AppException(status_code=404, detail="Target dataset not found.")

            features = await self.uow.dataset_features.get_intersecting_features(
                source_dataset_id=dataset_id,
                source_feature_id=feature_id,
                target_dataset_id=target_dataset_id,
            )

            return {
                "type": "FeatureCollection",
                "features": features,
            }


def _derive_name(filename: str) -> str:
    """Derive a human-friendly name from a filename."""
    name = filename
    for ext in (".geojson", ".json", ".geo.json"):
        if name.lower().endswith(ext):
            name = name[: -len(ext)]
            break
    return name.replace("_", " ").replace("-", " ").strip() or filename
