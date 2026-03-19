from uuid import UUID

from unittest.mock import patch

import pytest

from pushikoo.model.adapter import AdapterInstanceCreate, AdapterInstanceListFilter
from pushikoo.service.adapter import AdapterInstanceService
from pushikoo.service.base import ConflictException, NotFoundException


def _create_instance(adapter_name="test-adapter", identifier="inst-1"):
    with patch.object(AdapterInstanceService, "get_object_by_id", return_value=None):
        return AdapterInstanceService.create(
            AdapterInstanceCreate(adapter_name=adapter_name, identifier=identifier)
        )


def test_create_basic():
    result = _create_instance()
    assert result.adapter_name == "test-adapter"
    assert result.identifier == "inst-1"


def test_create_conflict():
    _create_instance()

    with pytest.raises(ConflictException):
        _create_instance()


def test_get_list_and_delete():
    first = _create_instance(adapter_name="a", identifier="1")
    _create_instance(adapter_name="b", identifier="2")

    found = AdapterInstanceService.get(first.id)
    assert found.id == first.id

    listed = AdapterInstanceService.list(AdapterInstanceListFilter(adapter_name="a"))
    assert listed.total == 1
    assert listed.items[0].identifier == "1"

    AdapterInstanceService.delete("a", "1")
    with pytest.raises(NotFoundException):
        AdapterInstanceService.get(first.id)


def test_get_and_delete_not_found():
    with pytest.raises(NotFoundException):
        AdapterInstanceService.get(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))

    with pytest.raises(NotFoundException):
        AdapterInstanceService.delete("missing", "missing")
