def test_system_config_crud(client):
    get_resp = client.get("/api/v1/system/config")
    assert get_resp.status_code == 200
    assert get_resp.json()["network"]["proxies"] == {}

    update_resp = client.put(
        "/api/v1/system/config",
        json={"network": {"proxies": {"http": "http://proxy"}}},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["network"]["proxies"]["http"] == "http://proxy"
