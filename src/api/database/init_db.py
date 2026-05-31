from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.api.config import DATABASE_PATH
from src.api.database import models  # noqa: F401
from src.api.database.session import Base, engine


def init_db() -> None:
    if engine.dialect.name == "sqlite":
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def main() -> None:
    init_db()
    target = str(DATABASE_PATH) if engine.dialect.name == "sqlite" else engine.url.render_as_string(hide_password=True)
    print(f"Database initialized ({engine.dialect.name}): {target}")


if __name__ == "__main__":
    main()
