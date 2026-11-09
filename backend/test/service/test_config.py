from unittest.mock import patch

from pydantic import BaseModel
from sqlmodel import Session

from pushikoo.db import Config as ConfigDB
from pushikoo.service.config import ConfigService


class DummyConfig(BaseModel):
    value: str = "default"
    count: int = 0


def test_get_default():
    service = ConfigService("dummy", DummyConfig)
    result = service.get()
    assert result == DummyConfig()


def test_set_and_overwrite_and_delete():
    service = ConfigService("dummy", DummyConfig)

    service.set(DummyConfig(value="first", count=1))
    assert service.get() == DummyConfig(value="first", count=1)

    service.set(DummyConfig(value="second", count=2))
    assert service.get() == DummyConfig(value="second", count=2)

    assert service.delete() is True
    assert service.get() == DummyConfig()
    assert service.delete() is False


def test_invalid_db_data_recovers_without_deleting(in_memory_engine):
    original = {"value": "preserved", "count": "bad"}
    with Session(in_memory_engine) as session:
        session.add(ConfigDB(key="dummy", value=original))
        session.commit()

    service = ConfigService("dummy", DummyConfig)

    with patch("pushikoo.service.warning.WarningService.issue") as issue:
        assert service.get() == DummyConfig(value="preserved", count=0)
        assert service.get() == DummyConfig(value="preserved", count=0)
        issue.assert_called_once()

    with Session(in_memory_engine) as session:
        assert session.get(ConfigDB, "dummy").value == original
