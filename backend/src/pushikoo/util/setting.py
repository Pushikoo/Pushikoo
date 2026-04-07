import os
from pathlib import Path
from secrets import token_hex
from typing import Annotated, Any, Literal

from pydantic import AnyUrl, BeforeValidator, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

CRON_SCHEDULER_MAX_WORKERS = 10
DATA_DIR = Path(os.environ.get("PUSHIKOO_DATA_DIR", "./data"))
CACHE_DIR = DATA_DIR / ".cache"
FILE_DIR = DATA_DIR / "files"

IMAGE_LINK_DEFAULT_EXPIRE_SECOND = 100 * 365 * 24 * 3600

DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
FILE_DIR.mkdir(parents=True, exist_ok=True)


def _parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list):
        return v
    raise ValueError(v)


def _parse_str_list(v: Any) -> list[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    if isinstance(v, list):
        return [str(i).strip() for i in v if str(i).strip()]
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="./.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 11589

    SECRET_TOKENS: list[str] = Field(default_factory=list)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    LOCAL_AUTH_DISABLED: bool = False

    ENVIRONMENT: Literal["local", "staging", "production"] = "production"

    BASE_HOST: str = Field(default="https://your.website.com")

    raw_cors_origins: Annotated[list[AnyUrl] | str, BeforeValidator(_parse_cors)] = (
        Field(
            default_factory=list,
            alias="CORS_ORIGINS",
        )
    )
    # ------------------------------------------------------------------

    # OIDC / SSO configuration
    SSO_CLIENT_ID: str | None = None
    SSO_CLIENT_SECRET: str | None = None
    SSO_ISSUER_URL: str | None = None
    ADMIN_USERS: Annotated[list[str] | str, BeforeValidator(_parse_str_list)] = Field(
        default_factory=list
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def CORS_ORIGINS(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.raw_cors_origins] + [
            self.BASE_HOST
        ]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SESSION_SECRET(self) -> str:
        if self.ENVIRONMENT == "local":
            return self.SSO_CLIENT_SECRET or "dev-secret"
        if self.SSO_CLIENT_SECRET:
            return self.SSO_CLIENT_SECRET
        return token_hex(32)


settings = Settings()  # type: ignore
