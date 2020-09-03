def test_get_resources(fastapi_client):
    r = fastapi_client.get("/resources")
    print(f"r.json = {r.json()}")
    assert len(r.json()) == 0
