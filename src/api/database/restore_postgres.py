from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

from sqlalchemy.engine import make_url


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.api.config import DATABASE_URL


class PostgresSettings(NamedTuple):
    username: str
    password: str | None
    host: str
    port: int
    database: str


class Command(NamedTuple):
    args: list[str]
    env: dict[str, str] | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore a PostgreSQL plain SQL backup with psql.")
    parser.add_argument("backup_file", type=Path)
    parser.add_argument("--execute", action="store_true", help="Actually restore the backup. Default is dry-run.")
    parser.add_argument("--prefer-local-tools", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        command = build_restore_command(args.backup_file, prefer_local_tools=args.prefer_local_tools)
        print_restore_command(command.args, backup_file=args.backup_file, dry_run=not args.execute)
        if not args.execute:
            return 0
        run_restore(command, args.backup_file)
    except ValueError as error:
        print(f"Restore failed: {error}")
        return 1
    except subprocess.CalledProcessError as error:
        print(f"Restore failed: psql exited with code {error.returncode}")
        if error.stderr:
            print(error.stderr.strip())
        return error.returncode

    print("Restore completed")
    return 0


def build_restore_command(backup_file: Path, *, prefer_local_tools: bool) -> Command:
    if not backup_file.exists():
        raise ValueError(f"Backup file not found: {backup_file}")
    if not backup_file.is_file():
        raise ValueError(f"Backup path is not a file: {backup_file}")

    settings = read_postgres_settings()
    if prefer_local_tools and shutil.which("psql"):
        return Command(
            args=[
                "psql",
                "--host",
                settings.host,
                "--port",
                str(settings.port),
                "--username",
                settings.username,
                "--dbname",
                settings.database,
                "--file",
                str(backup_file),
                "--set",
                "ON_ERROR_STOP=on",
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
            "psql",
            "--username",
            settings.username,
            "--dbname",
            settings.database,
            "--set",
            "ON_ERROR_STOP=on",
        ],
        env=None,
    )


def run_restore(command: Command, backup_file: Path) -> None:
    if command.args[:5] == ["docker", "compose", "exec", "-T", "postgres"]:
        with backup_file.open("rb") as input_file:
            subprocess.run(
                command.args,
                cwd=PROJECT_ROOT,
                env=command.env,
                stdin=input_file,
                stderr=subprocess.PIPE,
                check=True,
            )
        return

    subprocess.run(command.args, cwd=PROJECT_ROOT, env=command.env, stderr=subprocess.PIPE, check=True)


def print_restore_command(args: list[str], *, backup_file: Path, dry_run: bool) -> None:
    prefix = "Dry-run restore command" if dry_run else "Executing restore command"
    command_text = " ".join(args)
    if args[:5] == ["docker", "compose", "exec", "-T", "postgres"]:
        command_text = f"{command_text} < {backup_file}"
    print(f"{prefix}: {command_text}")
    if dry_run:
        print("Restore was not executed. Re-run with --execute to restore the database.")


def read_postgres_settings() -> PostgresSettings:
    url = make_url(DATABASE_URL)
    if not url.get_backend_name().startswith("postgresql"):
        raise ValueError("DATABASE_URL must point to PostgreSQL for restore")
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
