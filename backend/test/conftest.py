import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

import pushikoo.db as db_module
from pushikoo.service.adapter import AdapterInstanceService, AdapterService
from pushikoo.service.config import ConfigService
from pushikoo.service.pip import PIPService
from pushikoo.service.refresh import CronService, getter_get_timeline_continuous_failed_times
from pushikoo.util.setting import settings


@pytest.fixture(autouse=True)
def force_local_env(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "local")
    monkeypatch.setattr(settings, "LOCAL_AUTH_DISABLED", True)


@pytest.fixture()
def in_memory_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def patched_db(in_memory_engine, monkeypatch):
    def _get_session():
        return Session(in_memory_engine)

    monkeypatch.setattr(db_module, "engine", in_memory_engine)
    monkeypatch.setattr(db_module, "get_session", _get_session)
    yield in_memory_engine


@pytest.fixture(autouse=True)
def reset_shared_state():
    ConfigService._locks.clear()
    AdapterService.adapters.clear()
    AdapterService.adapter_versions.clear()
    AdapterService.adapter_metas.clear()
    AdapterInstanceService.instance_objects.clear()
    AdapterInstanceService.instance_versions.clear()
    getter_get_timeline_continuous_failed_times.clear()
    PIPService._uv_available = None
    yield
    ConfigService._locks.clear()
    AdapterService.adapters.clear()
    AdapterService.adapter_versions.clear()
    AdapterService.adapter_metas.clear()
    AdapterInstanceService.instance_objects.clear()
    AdapterInstanceService.instance_versions.clear()
    getter_get_timeline_continuous_failed_times.clear()
    try:
        CronService.close()
    except Exception:
        pass
