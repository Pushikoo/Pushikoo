import pytest
from fastapi.testclient import TestClient

from pushikoo.api import create_app
from pushikoo.service.refresh import CronService


@pytest.fixture(autouse=True)
def disable_cron_reload(monkeypatch):
    monkeypatch.setattr(CronService, "_reload", classmethod(lambda cls: None))


@pytest.fixture()
def app(patched_db):
    return create_app()


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        yield c
