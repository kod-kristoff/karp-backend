def test_healthz(client_scope_session):
    response = client_scope_session.get("/healthz")
    assert response.status == "200 OK"
