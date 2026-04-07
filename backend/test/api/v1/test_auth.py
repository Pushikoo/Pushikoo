from fastapi.testclient import TestClient

from pushikoo.util.setting import settings


def test_unauthenticated_when_not_local(monkeypatch, app):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    with TestClient(app) as client:
        response = client.get("/api/v1/messages")

    assert response.status_code == 401


def test_cookie_auth_when_not_local(monkeypatch, app):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SECRET_TOKENS", ["test-token"])
    with TestClient(app) as client:
        client.cookies.set("access_token", "test-token")
        response = client.get("/api/v1/messages")

    assert response.status_code == 200


def test_bearer_auth_still_supported_when_not_local(monkeypatch, app):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SECRET_TOKENS", ["test-token"])
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/messages",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 200
