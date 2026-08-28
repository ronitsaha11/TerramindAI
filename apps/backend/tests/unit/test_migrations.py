from pathlib import Path

from src.db.models import Base

VERSIONS_DIR = Path(__file__).parents[2] / "alembic" / "versions"
INITIAL_MIGRATION = VERSIONS_DIR / "20260725_01_initial_schema.py"


def _migration_sources() -> list[str]:
    return [
        path.read_text(encoding="utf-8") for path in sorted(VERSIONS_DIR.glob("*.py"))
    ]


def test_every_current_model_table_is_declared_by_some_migration():
    """A fresh clone must migrate to a schema that matches the models.

    This spans the whole revision chain rather than the initial migration
    alone: `datasets` and `dataset_features` arrived later in a90513d23268,
    which is the correct way to evolve an already-deployed schema. Pinning
    the guarantee to the bootstrap revision would forbid incremental
    migrations entirely.
    """
    sources = _migration_sources()

    for table_name in Base.metadata.tables:
        assert any(f'"{table_name}"' in source for source in sources), (
            f"No migration declares table {table_name!r}"
        )


def test_initial_migration_bootstraps_postgis_and_owner():
    """The bootstrap revision still owns the one-time environment setup."""
    source = INITIAL_MIGRATION.read_text(encoding="utf-8")

    assert "CREATE EXTENSION IF NOT EXISTS postgis" in source
    assert "development@terramind.local" in source
