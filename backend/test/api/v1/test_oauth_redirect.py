from pushikoo.api.v1.oauth import _safe_redirect_path


def test_safe_redirect_path_accepts_local_absolute_path():
    assert _safe_redirect_path("/ext/test?source=sso") == "/ext/test?source=sso"


def test_safe_redirect_path_rejects_external_url():
    assert _safe_redirect_path("https://example.com") is None
    assert _safe_redirect_path("//example.com") is None
    assert _safe_redirect_path("ext/test") is None
