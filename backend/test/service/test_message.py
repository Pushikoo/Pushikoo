from uuid import UUID

import pytest
from pushikoo_interface import Struct, StructText

from pushikoo.model.message import MessageCreate, MessageListFilter, MessageOrder, MessageUpdate
from pushikoo.service.base import ConflictException, NotFoundException
from pushikoo.service.message import MessageService


def _make_create(identifier="msg-1", getter="getter-a", ts=1700000000.0, text="hello"):
    return MessageCreate(
        message_identifier=identifier,
        getter_name=getter,
        ts=ts,
        content=Struct(content=[StructText(text=text)]),
    )


def test_create_and_get():
    created = MessageService.create(_make_create())

    found = MessageService.get(created.id)

    assert found.id == created.id
    assert found.message_identifier == "msg-1"


def test_create_duplicate_raises():
    MessageService.create(_make_create())

    with pytest.raises(ConflictException):
        MessageService.create(_make_create())


def test_get_not_found():
    with pytest.raises(NotFoundException):
        MessageService.get(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))


def test_list_empty():
    result = MessageService.list(MessageListFilter())
    assert result.total == 0
    assert result.items == []


def test_list_filter_and_pagination_and_keywords():
    MessageService.create(_make_create(identifier="a", getter="g1", ts=1, text="hello world"))
    MessageService.create(_make_create(identifier="b", getter="g1", ts=2, text="bye world"))
    MessageService.create(_make_create(identifier="c", getter="g2", ts=3, text="hello pushikoo"))

    filtered = MessageService.list(MessageListFilter(getter_name="g1"))
    assert filtered.total == 2

    ranged = MessageService.list(MessageListFilter(ts_from=2, ts_to=3, order=MessageOrder.TS_ASC))
    assert [item.message_identifier for item in ranged.items] == ["b", "c"]

    paged = MessageService.list(MessageListFilter(limit=1, offset=1, order=MessageOrder.TS_ASC))
    assert [item.message_identifier for item in paged.items] == ["b"]

    keyworded = MessageService.list(MessageListFilter(keywords="hello"))
    assert {item.message_identifier for item in keyworded.items} == {"a", "c"}


def test_update_message():
    created = MessageService.create(_make_create())

    updated = MessageService.update(
        created.id,
        MessageUpdate(
            message_identifier="msg-2",
            ts=1800000000.0,
            content=Struct(content=[StructText(text="updated")]),
        ),
    )

    assert updated.message_identifier == "msg-2"
    assert updated.ts == 1800000000.0
    assert updated.content.content[0].text == "updated"


def test_update_not_found():
    with pytest.raises(NotFoundException):
        MessageService.update(
            UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            MessageUpdate(message_identifier="x"),
        )


def test_delete_and_exists():
    created = MessageService.create(_make_create(identifier="exists-id"))

    assert MessageService.exists("getter-a", "exists-id") is True

    MessageService.delete(created.id)

    assert MessageService.exists("getter-a", "exists-id") is False
    with pytest.raises(NotFoundException):
        MessageService.get(created.id)
