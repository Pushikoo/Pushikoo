from unittest.mock import patch

from pushikoo_interface import Pusher

from pushikoo.service.adapter import AdapterInstanceService, AdapterService


class DummyPusher(Pusher):
    pass


def _instance_payload():
    return {"adapter_name": "push", "identifier": "warn-1"}


def test_warning_recipient_crud(client):
    with patch.object(AdapterInstanceService, "get_object_by_id", return_value=None):
        instance_resp = client.post("/api/v1/instances", json=_instance_payload())
    instance_id = instance_resp.json()["id"]

    with patch.object(AdapterService, "get_clsobj_by_name", return_value=DummyPusher):
        create_resp = client.post(
            "/api/v1/warnings/recipients",
            json={"adapter_instance_id": instance_id},
        )
        assert create_resp.status_code == 201

        list_resp = client.get("/api/v1/warnings/recipients")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 1

        delete_resp = client.delete(f"/api/v1/warnings/recipients/{instance_id}")
        assert delete_resp.status_code == 204
