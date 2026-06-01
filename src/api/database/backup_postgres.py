from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from sqlalchemy.engine import make_url


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.api.config import BACKUP_DIR, BACKUP_FILE_TEMPLATE, DATABASE_URL


class PostgresSettings(NamedTuple):
    username: str
    password: str | None
    host: str
    port: int
    database: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a PostgreSQL plain SQL backup with pg_dump.")
    parser.add_argument("--output-dir", type=Path, default=BACKUP_DIR)
    parser.add_argument("--filename")
    parser.add_argument("--prefer-local-tools", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        backup_path = create_backup(
            output_dir=args.output_dir,
            filename=args.filename,
            prefer_local_tools=args.prefer_local_tools,
        )
    except ValueError as error:
        print(f"Backup failed: {error}")
        return 1
    except subprocess.CalledProcessError as error:
        print(f"Backup failed: pg_dump exited with code {error.returncode}")
        if error.stderr:
            print(error.stderr.strip())
        return error.returncode

    print(f"Backup created: {backup_path}")
    return 0


def create_backup(*, output_dir: Path, filename: str | None, prefer_local_tools: bool) -> Path:
    settings = read_postgres_settings()
    output_dir.mkdir(parents=True, exist_ok=True)
    backup_path = output_dir / (filename or datetime.now().strftime(BACKUP_FILE_TEMPLATE))

    command = build_pg_dump_command(settings, prefer_local_tools=prefer_local_tools)
    with backup_path.open("wb") as output_file:
        subprocess.run(
            command.args,
            cwd=PROJECT_ROOT,
            env=command.env,
            stdout=output_file,
            stderr=subprocess.PIPE,
            text=False,
            check=True,
        )

    return backup_path


class Command(NamedTuple):
    args: list[str]
    env: dict[str, str] | None


def build_pg_dump_command(settings: PostgresSettings, *, prefer_local_tools: bool) -> Command:
    if prefer_local_tools and shutil.which("pg_dump"):
        return Command(
            args=[
                "pg_dump",
                "--host",
                settings.host,
                "--port",
                str(settings.port),
                "--username",
                settings.username,
                "--dbname",
                settings.database,
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-privileges",
            ],
            env=pg_env(settings),
        )

    return Command(
        args=[
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "pg_dump",
            "--username",
            settings.username,
            "--dbname",
            settings.database,
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
        ],
        env=None,
    )


def read_postgres_settings() -> PostgresSettings:
    url = make_url(DATABASE_URL)
    if not url.get_backend_name().startswith("postgresql"):
        raise ValueError("DATABASE_URL must point to PostgreSQL for pg_dump backup")
    if not url.username or not url.database:
        raise ValueError("DATABASE_URL must include PostgreSQL username and database name")

    return PostgresSettings(
        username=url.username,
        password=url.password,
        host=url.host or "localhost",
        port=url.port or 5432,
        database=url.database,
    )


def pg_env(settings: PostgresSettings) -> dict[str, str]:
    import os

    env = os.environ.copy()
    if settings.password:
        env["PGPASSWORD"] = settings.password
    return env


if __name__ == "__main__":
    raise SystemExit(main())
