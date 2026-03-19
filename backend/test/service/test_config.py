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


def test_invalid_db_data_falls_back_to_default(in_memory_engine):
    with Session(in_memory_engine) as session:
        session.add(ConfigDB(key="dummy", value={"count": "bad"}))
        session.commit()

    service = ConfigService("dummy", DummyConfig)

    assert service.get() == DummyConfig()

    with Session(in_memory_engine) as session:
        assert session.get(ConfigDB, "dummy") is None
