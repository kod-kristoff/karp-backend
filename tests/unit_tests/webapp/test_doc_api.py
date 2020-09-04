def test_get_yaml(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    print(f"{response.json()}")
    assert response.json()["info"]["title"] == "Karp API"
