from __future__ import annotations

from pathlib import Path
import sys

from sqlalchemy import inspect, text


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.api.database.session import engine


def migrate_postgresql() -> dict[str, str]:
    actions: dict[str, str] = {}

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_history_viewed_at TIMESTAMP"))
        actions["users_last_history_viewed_at"] = "created_or_existing"

    return actions


def migrate_sqlite() -> dict[str, str]:
    actions: dict[str, str] = {}

    with engine.begin() as connection:
        inspector = inspect(connection)
        existing_columns = {column["name"] for column in inspector.get_columns("users")}
        if "last_history_viewed_at" not in existing_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN last_history_viewed_at TIMESTAMP"))
            actions["users_last_history_viewed_at"] = "created"
        else:
            actions["users_last_history_viewed_at"] = "existing"

    return actions


def migrate_user_history_view_state() -> dict[str, str]:
    if engine.dialect.name == "postgresql":
        return migrate_postgresql()
    if engine.dialect.name == "sqlite":
        return migrate_sqlite()
    raise RuntimeError(f"Unsupported database dialect: {engine.dialect.name}")


def main() -> None:
    actions = migrate_user_history_view_state()
    print(f"User history view state migration completed ({engine.dialect.name}).")
    for key, value in actions.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
