from fastapi.testclient import TestClient

from pushikoo.util.setting import settings


def test_unauthenticated_when_not_local(monkeypatch, app):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    with TestClient(app) as client:
        response = client.get("/api/v1/messages")

    assert response.status_code == 401
