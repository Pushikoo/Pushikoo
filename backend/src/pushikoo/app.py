import os
import re
import sqlite3
import sys
from contextlib import closing, suppress
from datetime import datetime, timezone
from importlib.resources import as_file, files
from pathlib import Path
from typing import Optional

import uvicorn
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from loguru import logger
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from pushikoo.api import app
from pushikoo.db import engine as app_engine
from pushikoo.service.adapter import AdapterInstanceService, AdapterService
from pushikoo.service.refresh import CronService, FlowInstanceService
from pushikoo.util.env import is_running_from_source
from pushikoo.util.setting import DATA_DIR, settings


def _get_version() -> str | None:
    """Get version from package metadata."""
    try:
        from importlib.metadata import version

        return version("pushikoo")
    except Exception:
        return None


def _activate_venv() -> None:
    """
    Simulate virtual environment activation by modifying PATH.

    This ensures that commands installed in the venv's Scripts (Windows) or bin (Unix)
    directory can be executed as bare commands (e.g., 'pip' instead of 'python -m pip').
    """
    # sys.prefix points to the venv root when running inside a venv
    venv_root = Path(sys.prefix)

    # Determine the scripts directory based on the platform
    if sys.platform == "win32":
        scripts_dir = venv_root / "Scripts"
    else:
        scripts_dir = venv_root / "bin"

    if not scripts_dir.exists():
        return

    scripts_path = str(scripts_dir)
    current_path = os.environ.get("PATH", "")

    # Only add if not already at the front of PATH
    if not current_path.startswith(scripts_path):
        os.environ["PATH"] = scripts_path + os.pathsep + current_path

    # Set VIRTUAL_ENV environment variable (standard for activated venvs)
    os.environ["VIRTUAL_ENV"] = str(venv_root)


_MIGRATION_BACKUP_PATTERN = re.compile(
    r"^pushikoo-\d{8}T\d{12}Z-[A-Za-z0-9_.-]+\.db$"
)


def _backup_sqlite_database(
    database_path: Path, current_revision: str | None, head_revision: str
) -> Path:
    backup_dir = DATA_DIR / "backup"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    revision = current_revision or "none"
    backup_path = backup_dir / f"pushikoo-{timestamp}-{revision}.db"
    backup_complete = False

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        with (
            closing(sqlite3.connect(database_path)) as source,
            closing(sqlite3.connect(backup_path)) as destination,
        ):
            source.backup(destination)
        backup_complete = True

        backups = sorted(
            (
                path
                for path in backup_dir.iterdir()
                if path.is_file()
                and _MIGRATION_BACKUP_PATTERN.fullmatch(path.name)
            ),
            key=lambda path: path.name,
            reverse=True,
        )
        for old_backup in backups[5:]:
            old_backup.unlink()
    except Exception:
        if not backup_complete:
            with suppress(OSError):
                backup_path.unlink(missing_ok=True)
        logger.exception(
            "Failed to prepare SQLite backup before migration {} -> {}: {}",
            revision,
            head_revision,
            backup_path,
        )
        raise

    logger.info(
        "Backed up SQLite database before migration {} -> {}: {}",
        revision,
        head_revision,
        backup_path,
    )
    return backup_path


def db_upgrade_to_head(engine: Optional[Engine] = None) -> None:
    eng = engine or app_engine
    cfg = Config()
    scripts = files("pushikoo") / "alembic"
    with as_file(scripts) as script_path:
        cfg.set_main_option("script_location", str(script_path))
        script_directory = ScriptDirectory.from_config(cfg)
        head_revision = script_directory.get_current_head()

        database = eng.url.database
        is_memory_database = database in (None, "", ":memory:") or (
            isinstance(database, str) and "mode=memory" in database
        )
        database_path = Path(database) if database and not is_memory_database else None
        database_existed = database_path is not None and database_path.is_file()

        with eng.connect() as connection:
            migration_context = MigrationContext.configure(connection)
            current_revision = migration_context.get_current_revision()
            has_tables = bool(inspect(connection).get_table_names())

        has_pending_migrations = current_revision is None or any(
            script_directory.iterate_revisions(head_revision, current_revision)
        )
        if (
            eng.dialect.name == "sqlite"
            and database_existed
            and database_path is not None
            and has_pending_migrations
            and (current_revision is not None or has_tables)
        ):
            _backup_sqlite_database(database_path, current_revision, head_revision)

        with eng.connect() as connection:
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")


def _init_log():
    if settings.ENVIRONMENT != "local":
        logger.remove()
        logger.add(
            sys.stdout,
            level="INFO",
        )
    logger.add(
        "data/log/app.log",
        rotation="100 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8",
    )


def main() -> None:
    _activate_venv()
    _init_log()

    if version := _get_version():
        logger.info(f"Pushikoo v{version} started")
    else:
        logger.info("Pushikoo started")

    if settings.ENVIRONMENT == "local" and not is_running_from_source():
        logger.warning(
            "\n================================== ⚠️ LOCAL MODE ⚠️ ==================================\n"
            "Application is running in LOCAL mode. This mode disables production-level security "
            "checks and should NEVER be used in a production environment. If this instance is"
            " intended for production, please set environment $ENVIRONMENT=production or edit your"
            " .env file."
            "\n=======================================================================================\n"
        )
        exit(1)

    db_upgrade_to_head()
    AdapterService.ensure_load_adapter()
    AdapterInstanceService.ensure_load_all_instances()
    FlowInstanceService.recover()
    CronService.init()

    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
    CronService.close()
    logger.info("Pushikoo shutdown")
    os._exit(0)


if __name__ == "__main__":
    main()
