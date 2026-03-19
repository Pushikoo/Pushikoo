from unittest.mock import patch

from pushikoo.service.pip import PIPService


def test_pip_indexes_crud(client):
    url = "https://example.com/simple"

    create_resp = client.post(f"/api/v1/pip/indexes/{url}")
    assert create_resp.status_code == 201

    list_resp = client.get("/api/v1/pip/indexes")
    assert list_resp.status_code == 200
    assert list_resp.json() == [url]

    duplicate_resp = client.post(f"/api/v1/pip/indexes/{url}")
    assert duplicate_resp.status_code == 409

    delete_resp = client.delete(f"/api/v1/pip/indexes/{url}")
    assert delete_resp.status_code == 204


def test_pip_install_endpoint(client):
    with patch.object(
        PIPService,
        "install",
        return_value={"ok": True, "target": "demo", "output": "installed"},
    ):
        response = client.post("/api/v1/pip/pkgs/demo")
    assert response.status_code == 200
    assert response.json()["target"] == "demo"
