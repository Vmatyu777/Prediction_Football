from __future__ import annotations

from pathlib import Path
import sys

from sqlalchemy import inspect, text


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.api.database.session import engine


EXTERNAL_SOURCE_NAME = "API-FOOTBALL"
FK_CONSTRAINT_NAME = "fk_matches_external_source_id"
UNIQUE_CONSTRAINT_NAME = "uq_matches_external_identity"


def migrate_postgresql() -> dict[str, str]:
    actions: dict[str, str] = {}

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS external_sources (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) NOT NULL UNIQUE
                )
                """
            )
        )
        actions["external_sources_table"] = "created_or_existing"

        connection.execute(
            text(
                """
                INSERT INTO external_sources (name)
                VALUES (:name)
                ON CONFLICT (name) DO NOTHING
                """
            ),
            {"name": EXTERNAL_SOURCE_NAME},
        )
        actions["api_football_source"] = "created_or_existing"

        connection.execute(text("ALTER TABLE matches ADD COLUMN IF NOT EXISTS external_source_id INTEGER"))
        connection.execute(text("ALTER TABLE matches ADD COLUMN IF NOT EXISTS external_match_id VARCHAR(100)"))
        connection.execute(text("ALTER TABLE matches ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP"))
        actions["matches_columns"] = "created_or_existing"

        fk_exists = connection.execute(
            text(
                """
                SELECT 1
                FROM pg_constraint
                WHERE conname = :constraint_name
                """
            ),
            {"constraint_name": FK_CONSTRAINT_NAME},
        ).first()
        if fk_exists is None:
            connection.execute(
                text(
                    f"""
                    ALTER TABLE matches
                    ADD CONSTRAINT {FK_CONSTRAINT_NAME}
                    FOREIGN KEY (external_source_id)
                    REFERENCES external_sources(id)
                    """
                )
            )
            actions["matches_external_source_fk"] = "created"
        else:
            actions["matches_external_source_fk"] = "existing"

        unique_exists = connection.execute(
            text(
                """
                SELECT 1
                FROM pg_constraint
                WHERE conname = :constraint_name
                """
            ),
            {"constraint_name": UNIQUE_CONSTRAINT_NAME},
        ).first()
        if unique_exists is None:
            connection.execute(
                text(
                    f"""
                    ALTER TABLE matches
                    ADD CONSTRAINT {UNIQUE_CONSTRAINT_NAME}
                    UNIQUE (external_source_id, external_match_id)
                    """
                )
            )
            actions["matches_external_identity_unique"] = "created"
        else:
            actions["matches_external_identity_unique"] = "existing"

    return actions


def migrate_sqlite() -> dict[str, str]:
    actions: dict[str, str] = {}

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS external_sources (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(50) NOT NULL UNIQUE
                )
                """
            )
        )
        actions["external_sources_table"] = "created_or_existing"

        connection.execute(
            text("INSERT OR IGNORE INTO external_sources (name) VALUES (:name)"),
            {"name": EXTERNAL_SOURCE_NAME},
        )
        actions["api_football_source"] = "created_or_existing"

        inspector = inspect(connection)
        existing_columns = {column["name"] for column in inspector.get_columns("matches")}
        if "external_source_id" not in existing_columns:
            connection.execute(text("ALTER TABLE matches ADD COLUMN external_source_id INTEGER"))
            actions["matches_external_source_id"] = "created"
        else:
            actions["matches_external_source_id"] = "existing"

        if "external_match_id" not in existing_columns:
            connection.execute(text("ALTER TABLE matches ADD COLUMN external_match_id VARCHAR(100)"))
            actions["matches_external_match_id"] = "created"
        else:
            actions["matches_external_match_id"] = "existing"

        if "last_synced_at" not in existing_columns:
            connection.execute(text("ALTER TABLE matches ADD COLUMN last_synced_at TIMESTAMP"))
            actions["matches_last_synced_at"] = "created"
        else:
            actions["matches_last_synced_at"] = "existing"

        actions["matches_external_source_fk"] = "skipped_sqlite_alter_table_limit"
        actions["matches_external_identity_unique"] = "skipped_sqlite_alter_table_limit"

    return actions


def migrate_external_sources() -> dict[str, str]:
    if engine.dialect.name == "postgresql":
        return migrate_postgresql()
    if engine.dialect.name == "sqlite":
        return migrate_sqlite()
    raise RuntimeError(f"Unsupported database dialect: {engine.dialect.name}")


def main() -> None:
    actions = migrate_external_sources()
    print(f"External source migration completed ({engine.dialect.name}).")
    for key, value in actions.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
