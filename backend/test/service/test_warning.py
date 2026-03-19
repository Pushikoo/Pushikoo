from uuid import UUID

from unittest.mock import patch

import pytest
from pushikoo_interface import Pusher

from pushikoo.model.adapter import AdapterInstanceCreate
from pushikoo.service.adapter import AdapterInstanceService, AdapterService
from pushikoo.service.base import ConflictException, InvalidInputException, NotFoundException
from pushikoo.service.warning import WarningService


class DummyPusher(Pusher):
    pass


class DummyGetter:
    pass


def _create_instance():
    with patch.object(AdapterInstanceService, "get_object_by_id", return_value=None):
        return AdapterInstanceService.create(
            AdapterInstanceCreate(adapter_name="push", identifier="warn-1")
        )


def test_warning_recipient_crud():
    instance = _create_instance()

    with patch.object(AdapterService, "get_clsobj_by_name", return_value=DummyPusher):
        added = WarningService.add_recipient(instance.id)
        assert added.id == instance.id

        listed = WarningService.list_recipients()
        assert listed.total == 1
        assert listed.items[0].id == instance.id

        with pytest.raises(ConflictException):
            WarningService.add_recipient(instance.id)

        WarningService.remove_recipient(instance.id)
        assert WarningService.list_recipients().total == 0


def test_warning_recipient_rejects_non_pusher():
    instance = _create_instance()

    with patch.object(AdapterService, "get_clsobj_by_name", return_value=DummyGetter):
        with pytest.raises(InvalidInputException):
            WarningService.add_recipient(instance.id)


def test_warning_recipient_not_found():
    with pytest.raises(NotFoundException):
        WarningService.remove_recipient(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
