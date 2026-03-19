import pytest


@pytest.fixture(autouse=True)
def use_in_memory_db(patched_db):
    yield
