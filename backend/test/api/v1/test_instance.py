from unittest.mock import patch

from pushikoo.service.adapter import AdapterInstanceService


def _payload(adapter_name="pushikoo-adapter-testgetter", identifier="inst-1"):
    return {"adapter_name": adapter_name, "identifier": identifier}


def test_instance_crud(client):
    with patch.object(AdapterInstanceService, "get_object_by_id", return_value=None):
        create_resp = client.post("/api/v1/instances", json=_payload())
    assert create_resp.status_code == 201
    instance_id = create_resp.json()["id"]

    list_resp = client.get("/api/v1/instances")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    get_config_resp = client.get(f"/api/v1/instances/{instance_id}/config")
    assert get_config_resp.status_code == 200

    delete_resp = client.delete(f"/api/v1/instances/{instance_id}")
    assert delete_resp.status_code == 204


def test_instance_conflict_and_not_found(client):
    with patch.object(AdapterInstanceService, "get_object_by_id", return_value=None):
        first = client.post("/api/v1/instances", json=_payload(adapter_name="same", identifier="dup"))
        second = client.post("/api/v1/instances", json=_payload(adapter_name="same", identifier="dup"))
    assert first.status_code == 201
    assert second.status_code == 409

    missing_resp = client.delete("/api/v1/instances/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert missing_resp.status_code == 404
