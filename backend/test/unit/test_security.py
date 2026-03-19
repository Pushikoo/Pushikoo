from pushikoo.api.security import _as_key_list


def test_as_key_list_with_none():
    assert _as_key_list(None) == []


def test_as_key_list_with_empty_string():
    assert _as_key_list("") == []


def test_as_key_list_with_single_token():
    assert _as_key_list("abc") == ["abc"]


def test_as_key_list_with_csv():
    assert _as_key_list("a, b , c") == ["a", "b", "c"]


def test_as_key_list_with_sequence():
    assert _as_key_list(["a", " b"]) == ["a", "b"]


def test_as_key_list_ignores_empty_items():
    assert _as_key_list("a,,b") == ["a", "b"]
