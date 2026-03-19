from fastapi.testclient import TestClient

from pushikoo.util.setting import settings


def _msg_payload(identifier="m1", getter="g1", ts=1700000000.0, text="hello"):
    return {
        "message_identifier": identifier,
        "getter_name": getter,
        "ts": ts,
        "content": {"content": [{"type": "text", "text": text}]},
    }


def test_message_crud(client):
    create_resp = client.post("/api/v1/messages", json=_msg_payload())
    assert create_resp.status_code == 201
    message_id = create_resp.json()["id"]

    list_resp = client.get("/api/v1/messages")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    get_resp = client.get(f"/api/v1/messages/{message_id}")
    assert get_resp.status_code == 200

    update_resp = client.patch(
        f"/api/v1/messages/{message_id}",
        json={"message_identifier": "m2"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["message_identifier"] == "m2"

    delete_resp = client.delete(f"/api/v1/messages/{message_id}")
    assert delete_resp.status_code == 204


def test_message_filters_and_conflict(client):
    client.post("/api/v1/messages", json=_msg_payload(identifier="a", getter="g1", text="hello world"))
    client.post("/api/v1/messages", json=_msg_payload(identifier="b", getter="g2", text="bye world"))

    filter_resp = client.get("/api/v1/messages", params={"getter_name": "g1", "keywords": "hello"})
    assert filter_resp.status_code == 200
    assert filter_resp.json()["total"] == 1

    conflict_resp = client.post("/api/v1/messages", json=_msg_payload(identifier="a", getter="g1"))
    assert conflict_resp.status_code == 409


def test_message_not_found_and_auth(app, client, monkeypatch):
    missing_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    not_found_resp = client.get(f"/api/v1/messages/{missing_id}")
    assert not_found_resp.status_code == 404

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    with TestClient(app) as authless:
        auth_resp = authless.get("/api/v1/messages")
    assert auth_resp.status_code == 401
