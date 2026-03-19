import pytest
from pushikoo_interface import Detail, Struct, StructText

from pushikoo.service.base import InvalidInputException
from pushikoo.service.message import MessageService


def test_extract_text_empty():
    assert MessageService._extract_text_from_struct(None) == ""


def test_extract_text_basic():
    struct = Struct(content=[StructText(text="hello")])
    assert MessageService._extract_text_from_struct(struct) == "hello"


def test_template_v1_basic():
    detail = Detail(title="Title", content="Body", ts=1700000000.0)

    result = MessageService.Template.v1(detail)
    text = " ".join(item.text for item in result.content if hasattr(item, "text"))

    assert "Title" in text
    assert "Body" in text


def test_template_v1_with_author_and_url():
    detail = Detail(
        title="T",
        content="C",
        ts=1700000000.0,
        author_name="Alice",
        url="https://example.com",
    )

    result = MessageService.Template.v1(detail)
    text = " ".join(item.text for item in result.content if hasattr(item, "text"))

    assert "Alice" in text
    assert "https://example.com" in text


def test_template_v1_with_struct_content():
    inner = Struct(content=[StructText(text="inner text")])
    detail = Detail(title="T", content=inner, ts=1700000000.0)

    result = MessageService.Template.v1(detail)
    text = " ".join(item.text for item in result.content if hasattr(item, "text"))

    assert "inner text" in text


def test_template_v1_invalid_content_raises():
    detail = Detail.model_construct(title="T", content=123, ts=1700000000.0)

    with pytest.raises(InvalidInputException):
        MessageService.Template.v1(detail)
