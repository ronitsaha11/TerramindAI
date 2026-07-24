"""Create the initial TerraMind schema and development owner.

Revision ID: 20260725_01
Revises:
Create Date: 2026-07-25 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260725_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEVELOPMENT_OWNER_ID = "00000000-0000-0000-0000-000000000001"
DEVELOPMENT_OWNER_EMAIL = "development@terramind.local"

project_status = postgresql.ENUM(
    "ACTIVE", "ARCHIVED", name="projectstatus_enum", create_type=False
)
job_status = postgresql.ENUM(
    "QUEUED",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    name="jobstatus_enum",
    create_type=False,
)
job_type = postgresql.ENUM(
    "SEGMENTATION",
    "CHANGE_DETECTION",
    "FOREST_ANALYSIS",
    "DATA_IMPORT",
    "REPORT_GENERATION",
    name="jobtype_enum",
    create_type=False,
)
prediction_type = postgresql.ENUM(
    "SEGMENTATION_MASK",
    "CHANGE_MAP",
    "VEGETATION_INDEX",
    name="predictiontype_enum",
    create_type=False,
)
report_format = postgresql.ENUM(
    "PDF", "JSON", "CSV", name="reportformat_enum", create_type=False
)
audit_resource_type = postgresql.ENUM(
    "PROJECT",
    "REGION",
    "JOB",
    "PREDICTION",
    "REPORT",
    name="auditresourcetype_enum",
    create_type=False,
)


def _entity_columns() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    for enum_type in (
        project_status,
        job_status,
        job_type,
        prediction_type,
        report_format,
        audit_resource_type,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        *_entity_columns(),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "satellite_scenes",
        *_entity_columns(),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("scene_id", sa.String(length=255), nullable=False),
        sa.Column("acquisition_date", sa.DateTime(), nullable=False),
        sa.Column("cloud_cover", sa.Float(), nullable=True),
        sa.Column("bbox", sa.JSON(), nullable=True),
        sa.Column("stac_url", sa.String(length=1024), nullable=True),
        sa.Column("cog_url", sa.String(length=1024), nullable=True),
        sa.Column("resolution", sa.Float(), nullable=True),
        sa.Column("bands", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column(
            "geometry",
            Geometry(geometry_type="POLYGON", srid=4326, spatial_index=False),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_satellite_scenes_scene_id", "satellite_scenes", ["scene_id"], unique=True
    )
    op.create_index(
        "ix_satellite_scenes_acquisition_date", "satellite_scenes", ["acquisition_date"]
    )
    op.create_index(
        "idx_satellite_scenes_geometry",
        "satellite_scenes",
        ["geometry"],
        unique=False,
        postgresql_using="gist",
    )

    op.create_table(
        "projects",
        *_entity_columns(),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", project_status, nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("owner_id", "name", name="uq_project_owner_name"),
    )
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])

    op.create_table(
        "project_members",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "user_id"),
    )

    op.create_table(
        "regions",
        *_entity_columns(),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "geometry",
            Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("area_sq_km", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "name", name="uq_region_project_name"),
    )
    op.create_index("ix_regions_project_id", "regions", ["project_id"])
    op.create_index(
        "idx_regions_geometry",
        "regions",
        ["geometry"],
        unique=False,
        postgresql_using="gist",
    )

    op.create_table(
        "jobs",
        *_entity_columns(),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("job_type", job_type, nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_jobs_project_id", "jobs", ["project_id"])
    op.create_index("ix_jobs_region_id", "jobs", ["region_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_celery_task_id", "jobs", ["celery_task_id"])

    op.create_table(
        "predictions",
        *_entity_columns(),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prediction_type", prediction_type, nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("artifact_uri", sa.String(length=1024), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_predictions_job_id", "predictions", ["job_id"])

    op.create_table(
        "reports",
        *_entity_columns(),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("format", report_format, nullable=False),
        sa.Column("storage_uri", sa.String(length=1024), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["prediction_id"], ["predictions.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_reports_project_id", "reports", ["project_id"])
    op.create_index("ix_reports_prediction_id", "reports", ["prediction_id"])

    op.create_table(
        "lineage_records",
        *_entity_columns(),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scene_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("preprocessing", postgresql.JSONB(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("git_commit_sha", sa.String(length=40), nullable=True),
        sa.Column("software_version", sa.String(length=50), nullable=True),
        sa.Column("tile_size", sa.Integer(), nullable=True),
        sa.Column("crs", sa.String(length=20), nullable=True),
        sa.Column("inference_time_ms", sa.Integer(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["prediction_id"], ["predictions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["scene_id"], ["satellite_scenes.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_lineage_records_prediction_id", "lineage_records", ["prediction_id"]
    )
    op.create_index("ix_lineage_records_scene_id", "lineage_records", ["scene_id"])

    op.create_table(
        "audit_logs",
        *_entity_columns(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_type", audit_resource_type, nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"])

    op.execute(
        sa.text(
            """
            INSERT INTO users (id, email, name, role)
            VALUES (:id, :email, 'Development Owner', 'developer')
            ON CONFLICT (id) DO NOTHING
            """
        ).bindparams(id=DEVELOPMENT_OWNER_ID, email=DEVELOPMENT_OWNER_EMAIL)
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_resource_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_lineage_records_scene_id", table_name="lineage_records")
    op.drop_index("ix_lineage_records_prediction_id", table_name="lineage_records")
    op.drop_table("lineage_records")
    op.drop_index("ix_reports_prediction_id", table_name="reports")
    op.drop_index("ix_reports_project_id", table_name="reports")
    op.drop_table("reports")
    op.drop_index("ix_predictions_job_id", table_name="predictions")
    op.drop_table("predictions")
    op.drop_index("ix_jobs_celery_task_id", table_name="jobs")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_region_id", table_name="jobs")
    op.drop_index("ix_jobs_project_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("idx_regions_geometry", table_name="regions")
    op.drop_index("ix_regions_project_id", table_name="regions")
    op.drop_table("regions")
    op.drop_table("project_members")
    op.drop_index("ix_projects_owner_id", table_name="projects")
    op.drop_table("projects")
    op.drop_index("idx_satellite_scenes_geometry", table_name="satellite_scenes")
    op.drop_index("ix_satellite_scenes_acquisition_date", table_name="satellite_scenes")
    op.drop_index("ix_satellite_scenes_scene_id", table_name="satellite_scenes")
    op.drop_table("satellite_scenes")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    for enum_type in (
        audit_resource_type,
        report_format,
        prediction_type,
        job_type,
        job_status,
        project_status,
    ):
        enum_type.drop(bind, checkfirst=True)
