from unittest.mock import patch

from pushikoo.model.adapter import AdapterInstanceCreate
from pushikoo.service.adapter import AdapterInstanceService


def _create_instance(adapter_name, identifier):
    with patch.object(AdapterInstanceService, "get_object_by_id", return_value=None):
        return AdapterInstanceService.create(
            AdapterInstanceCreate(adapter_name=adapter_name, identifier=identifier)
        )


def test_flow_crud(client):
    getter = _create_instance("getter", "g1")
    pusher = _create_instance("pusher", "p1")

    create_resp = client.post(
        "/api/v1/flows",
        json={"name": "test-flow", "nodes": [str(getter.id), str(pusher.id)]},
    )
    assert create_resp.status_code == 201
    flow_id = create_resp.json()["id"]

    list_resp = client.get("/api/v1/flows")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    get_resp = client.get(f"/api/v1/flows/{flow_id}")
    assert get_resp.status_code == 200

    update_resp = client.put(f"/api/v1/flows/{flow_id}", json={"name": "updated"})
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "updated"

    delete_resp = client.delete(f"/api/v1/flows/{flow_id}")
    assert delete_resp.status_code == 204


def test_flow_get_not_found(client):
    response = client.get("/api/v1/flows/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert response.status_code == 404
