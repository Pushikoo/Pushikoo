from unittest.mock import patch

from pushikoo.model.adapter import AdapterInstanceCreate
from pushikoo.service.adapter import AdapterInstanceService


def _create_instance(adapter_name, identifier):
    with patch.object(AdapterInstanceService, "get_object_by_id", return_value=None):
        return AdapterInstanceService.create(
            AdapterInstanceCreate(adapter_name=adapter_name, identifier=identifier)
        )


def test_cron_crud(client):
    getter = _create_instance("getter", "g1")
    pusher = _create_instance("pusher", "p1")
    flow_resp = client.post(
        "/api/v1/flows",
        json={"name": "flow", "nodes": [str(getter.id), str(pusher.id)]},
    )
    flow_id = flow_resp.json()["id"]

    create_resp = client.post(
        "/api/v1/crons",
        json={"flow_id": flow_id, "cron": "0 * * * *", "enabled": True},
    )
    assert create_resp.status_code == 201
    cron_id = create_resp.json()["id"]

    list_resp = client.get("/api/v1/crons")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    delete_resp = client.delete(f"/api/v1/crons/{cron_id}")
    assert delete_resp.status_code == 204
