from fastapi import Depends
from fastapi.testclient import TestClient

from pushikoo.service.adapter import adapter_container_app
from pushikoo.util.auth import verify_token_or_login_redirect
from pushikoo.util.setting import settings


def test_ext_browser_unauthorized_redirects_to_login(app, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SECRET_TOKENS", [])

    @adapter_container_app.get("/test-unauthorized-redirect")
    async def protected(_: str = Depends(verify_token_or_login_redirect)):
        return {"ok": True}

    try:
        with TestClient(app) as client:
            response = client.get(
                "/ext/test-unauthorized-redirect?source=browser",
                headers={"Accept": "text/html"},
                follow_redirects=False,
            )

        assert response.status_code == 302
        assert (
            response.headers["location"]
            == "/login?redirect=%2Fext%2Ftest-unauthorized-redirect%3Fsource%3Dbrowser"
        )
    finally:
        adapter_container_app.router.routes = [
            route
            for route in adapter_container_app.router.routes
            if getattr(route, "path", "") != "/test-unauthorized-redirect"
        ]


def test_ext_api_unauthorized_stays_401(app, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SECRET_TOKENS", [])

    @adapter_container_app.get("/test-unauthorized-api")
    async def protected(_: str = Depends(verify_token_or_login_redirect)):
        return {"ok": True}

    try:
        with TestClient(app) as client:
            response = client.get(
                "/ext/test-unauthorized-api",
                headers={"Accept": "application/json"},
                follow_redirects=False,
            )

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
    finally:
        adapter_container_app.router.routes = [
            route
            for route in adapter_container_app.router.routes
            if getattr(route, "path", "") != "/test-unauthorized-api"
        ]
