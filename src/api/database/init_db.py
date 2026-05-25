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
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def main() -> None:
    init_db()
    print(f"SQLite database initialized: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
