def test_get_entry_w_slash(client):
    response = client.get("/entries/res/tu/or/")
    assert response.status_code == 200
