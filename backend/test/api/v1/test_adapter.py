def test_list_adapters(client):
    response = client.get("/api/v1/adapters")
    assert response.status_code == 200
    assert response.json()

def test_get_adapter_config_schema(client):
    response = client.get(
        "/api/v1/adapters/pushikoo-adapter-testgetter/config/schema"
    )
    assert response.status_code == 200
    assert response.json()["type"] == "object"
