def test_get_resources(client):
    r = client.get("/resources")
    print(f"r.json = {r.json()}")
    assert len(r.json()) == 0
