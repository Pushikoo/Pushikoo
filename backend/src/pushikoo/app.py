import os
import sys
from importlib.resources import as_file, files
from pathlib import Path
from typing import Optional

import uvicorn
from alembic import command
from alembic.config import Config
from loguru import logger
from sqlalchemy.engine import Engine

from pushikoo.api import app
from pushikoo.db import engine as app_engine
from pushikoo.service.refresh import CronService
from pushikoo.util.setting import settings


def db_upgrade_to_head(engine: Optional[Engine] = None) -> None:
    eng = engine or app_engine
    cfg = Config()
    scripts = files("pushikoo") / "alembic"
    with as_file(scripts) as script_path:
        cfg.set_main_option("script_location", str(script_path))
        with eng.connect() as connection:
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")


def main() -> None:
    logger.info("Pushikoo started")
    if settings.ENVIRONMENT != "local":
        logger.remove()
        logger.add(
            sys.stdout,
            level="INFO",
        )

    if settings.ENVIRONMENT == "local" and not Path("pyproject.toml").exists():
        logger.warning(
            "\n================================== ⚠️ LOCAL MODE ⚠️ ==================================\n"
            "Application is running in LOCAL mode. This mode disables production-level security "
            "checks and should NEVER be used in a production environment. If this instance is"
            " intended for production, please set environment $ENVIRONMENT=production or edit your"
            " .env file."
            "\n=======================================================================================\n"
        )
        exit(1)

    logger.add(
        "data/log/app.log",
        rotation="100 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8",
    )

    db_upgrade_to_head()
    # Thread(target=AdapterInstanceService.init).start()
    CronService.init()

    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
    CronService.close()
    logger.info("Pushikoo shutdown")
    os._exit(0)


if __name__ == "__main__":
    main()
