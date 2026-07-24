from pathlib import Path

from src.db.models import Base


def test_initial_migration_declares_every_current_model_table():
    """Keep the bootstrap migration aligned with models in a fresh clone."""
    migration = (
        Path(__file__).parents[2]
        / "alembic"
        / "versions"
        / "20260725_01_initial_schema.py"
    )
    source = migration.read_text(encoding="utf-8")

    for table_name in Base.metadata.tables:
        assert f'"{table_name}"' in source

    assert "CREATE EXTENSION IF NOT EXISTS postgis" in source
    assert "development@terramind.local" in source
