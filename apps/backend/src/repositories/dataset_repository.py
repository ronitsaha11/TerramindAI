import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.dataset import Dataset
from src.db.models.dataset_feature import DatasetFeature
from src.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Dataset)

    async def find_by_project(self, project_id: uuid.UUID) -> Sequence[Dataset]:
        result = await self.session.execute(
            select(Dataset)
            .where(Dataset.project_id == project_id)
            .order_by(Dataset.created_at.desc())
        )
        return result.scalars().all()


class DatasetFeatureRepository(BaseRepository[DatasetFeature]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DatasetFeature)

    async def bulk_create(self, features_data: list[dict]) -> None:
        import uuid

        from sqlalchemy import text

        # Ensure all features have an ID so we don't rely on server
        # defaults during executemany
        for f in features_data:
            if "id" not in f:
                f["id"] = uuid.uuid4()

        query = text("""
            INSERT INTO dataset_features (id, dataset_id, geometry, properties)
            VALUES (:id, :dataset_id, ST_GeomFromEWKT(:geometry), :properties)
        """)
        await self.session.execute(query, features_data)

    async def get_geojson_features(self, dataset_id: uuid.UUID) -> list[dict]:
        import json

        from sqlalchemy import text

        query = text("""
            SELECT id, ST_AsGeoJSON(geometry) as geom, properties 
            FROM dataset_features 
            WHERE dataset_id = :dataset_id
        """)
        result = await self.session.execute(query, {"dataset_id": dataset_id})
        features = []
        for row in result:
            feature_id, geom_str, props_dict = row.id, row.geom, row.properties
            if not geom_str:
                continue

            # ST_AsGeoJSON returns a string, we need to parse it back into a dict
            geom_dict = json.loads(geom_str)
            props_dict = props_dict if props_dict else {}

            features.append(
                {
                    "type": "Feature",
                    "id": str(feature_id),
                    "geometry": geom_dict,
                    "properties": props_dict,
                }
            )
        return features

    async def get_nearby_features(
        self,
        dataset_id: uuid.UUID,
        lon: float,
        lat: float,
        radius_meters: float,
    ) -> list[dict]:
        """Return features within radius_meters of (lon, lat).

        Uses ST_DWithin with ::geography casts so the radius is
        interpreted in real meters on the WGS-84 ellipsoid.
        The GiST index on the geometry column is used automatically
        by PostGIS when the query planner deems it beneficial.
        """
        import json

        from sqlalchemy import text

        query = text("""
            SELECT id, ST_AsGeoJSON(geometry) AS geom, properties
            FROM dataset_features
            WHERE dataset_id = :dataset_id
              AND ST_DWithin(
                    geometry::geography,
                    ST_MakePoint(:lon, :lat)::geography,
                    :radius_meters
                  )
        """)
        result = await self.session.execute(
            query,
            {
                "dataset_id": dataset_id,
                "lon": lon,
                "lat": lat,
                "radius_meters": radius_meters,
            },
        )
        features = []
        for row in result:
            feature_id, geom_str, props_dict = row.id, row.geom, row.properties
            if not geom_str:
                continue
            geom_dict = json.loads(geom_str)
            props_dict = props_dict if props_dict else {}
            features.append(
                {
                    "type": "Feature",
                    "id": str(feature_id),
                    "geometry": geom_dict,
                    "properties": props_dict,
                }
            )
        return features

    async def get_intersecting_features(
        self,
        source_dataset_id: uuid.UUID,
        source_feature_id: uuid.UUID,
        target_dataset_id: uuid.UUID,
    ) -> list[dict]:
        """Return features of *target_dataset_id* that intersect a feature of
        *source_dataset_id*.

        ST_Intersects is used rather than ST_Contains because overlap between
        two independent datasets is partial by nature. The source feature is
        excluded so a dataset compared against itself does not trivially match.
        """
        import json

        from sqlalchemy import text

        query = text("""
            WITH source_feature AS (
                SELECT geometry
                FROM dataset_features
                WHERE id = :source_feature_id AND dataset_id = :source_dataset_id
            )
            SELECT f.id, ST_AsGeoJSON(f.geometry) AS geom, f.properties
            FROM dataset_features f, source_feature sf
            WHERE f.dataset_id = :target_dataset_id
              AND f.id != :source_feature_id
              AND ST_Intersects(sf.geometry, f.geometry)
        """)

        result = await self.session.execute(
            query,
            {
                "source_dataset_id": source_dataset_id,
                "source_feature_id": source_feature_id,
                "target_dataset_id": target_dataset_id,
            },
        )

        features = []
        for row in result:
            feature_id, geom_str, props_dict = row.id, row.geom, row.properties
            if not geom_str:
                continue
            geom_dict = json.loads(geom_str)
            props_dict = props_dict if props_dict else {}
            features.append(
                {
                    "type": "Feature",
                    "id": str(feature_id),
                    "geometry": geom_dict,
                    "properties": props_dict,
                }
            )
        return features

    async def get_contained_features(
        self,
        dataset_id: uuid.UUID,
        polygon_feature_id: uuid.UUID,
    ) -> list[dict]:
        """Return features contained within the specified polygon feature."""
        import json

        from sqlalchemy import text

        # We use a subquery to get the source polygon's geometry,
        # then use ST_Contains (or ST_Intersects, but ST_Contains matches the prompt)
        # to find all OTHER features in the same dataset that are inside it.
        query = text("""
            WITH source_polygon AS (
                SELECT geometry 
                FROM dataset_features 
                WHERE id = :polygon_feature_id AND dataset_id = :dataset_id
            )
            SELECT f.id, ST_AsGeoJSON(f.geometry) AS geom, f.properties
            FROM dataset_features f, source_polygon sp
            WHERE f.dataset_id = :dataset_id
              AND f.id != :polygon_feature_id
              AND ST_Contains(sp.geometry, f.geometry)
        """)

        result = await self.session.execute(
            query,
            {
                "dataset_id": dataset_id,
                "polygon_feature_id": polygon_feature_id,
            },
        )

        features = []
        for row in result:
            feature_id, geom_str, props_dict = row.id, row.geom, row.properties
            if not geom_str:
                continue
            geom_dict = json.loads(geom_str)
            props_dict = props_dict if props_dict else {}
            features.append(
                {
                    "type": "Feature",
                    "id": str(feature_id),
                    "geometry": geom_dict,
                    "properties": props_dict,
                }
            )
        return features

    async def find_by_name(
        self,
        project_id: uuid.UUID,
        name_query: str,
        limit: int = 10,
    ) -> list[dict]:
        """Return features across a project whose name matches *name_query*.

        This is the bridge between a place name and a feature the spatial
        primitives can actually take: they address rows by UUID, while natural
        language only ever supplies a name. Matching is a case-insensitive
        substring so "Lalbagh" finds "Lalbagh Botanical Gardens", and the caller
        is handed every match rather than a best guess.

        Shorter names sort first, so an exact name outranks one that merely
        contains it.
        """
        from sqlalchemy import text

        query = text("""
            SELECT
                f.id                                    AS feature_id,
                f.properties->>'name'                   AS feature_name,
                f.dataset_id                            AS dataset_id,
                d.name                                  AS dataset_name,
                f.properties->>'category'               AS category,
                ST_GeometryType(f.geometry)             AS geometry_type,
                ST_X(ST_Centroid(f.geometry))           AS lon,
                ST_Y(ST_Centroid(f.geometry))           AS lat
            FROM dataset_features f
            JOIN datasets d ON d.id = f.dataset_id
            WHERE d.project_id = :project_id
              AND f.properties->>'name' ILIKE :pattern
            ORDER BY length(f.properties->>'name'), f.properties->>'name'
            LIMIT :limit
        """)
        result = await self.session.execute(
            query,
            {
                "project_id": project_id,
                "pattern": f"%{name_query}%",
                "limit": limit,
            },
        )
        return [dict(row._mapping) for row in result]

    async def summarise_project(self, project_id: uuid.UUID) -> list[dict]:
        """Return each dataset in a project with its distinct category values.

        This is the vocabulary handed to the language model. It is names and
        counts only - deliberately no geometry, coordinates or identifiers.
        """
        from sqlalchemy import text

        query = text("""
            SELECT
                d.name AS dataset_name,
                COUNT(f.id) AS feature_count,
                COALESCE(
                    ARRAY_AGG(DISTINCT f.properties->>'category')
                        FILTER (WHERE f.properties->>'category' IS NOT NULL),
                    '{}'
                ) AS categories
            FROM datasets d
            LEFT JOIN dataset_features f ON f.dataset_id = d.id
            WHERE d.project_id = :project_id
            GROUP BY d.id, d.name
            ORDER BY d.name
        """)
        result = await self.session.execute(query, {"project_id": project_id})
        return [dict(row._mapping) for row in result]
