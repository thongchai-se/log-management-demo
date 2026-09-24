"""API tests that do not require OpenSearch (auth surface)."""

from __future__ import annotations


def test_login_admin_ok(api_client):
    res = api_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"] == "demo-token-admin"
    assert body["role"] == "admin"
    assert body["tenant"] is None


def test_login_viewer_ok(api_client):
    res = api_client.post(
        "/api/auth/login",
        json={"username": "viewer", "password": "viewer123"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["role"] == "viewer"
    assert body["tenant"] == "demoA"


def test_login_invalid_password(api_client):
    res = api_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert res.status_code == 401


def test_health_endpoint(api_client):
    res = api_client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["api"] == "healthy"
    assert "opensearch" in body


def test_protected_routes_require_auth(api_client):
    # HTTPBearer returns 403 when header missing on some versions, 401 when invalid
    for path in ("/api/logs", "/api/dashboard", "/api/alerts"):
        assert api_client.get(path).status_code in (401, 403)
    assert api_client.post("/api/ingest", json={"tenant": "demoA"}).status_code in (401, 403)


def test_viewer_cannot_ingest(api_client, viewer_headers):
    res = api_client.post(
        "/api/ingest",
        headers=viewer_headers,
        json={
            "tenant": "demoA",
            "source": "api",
            "event_type": "should_fail",
            "user": "viewer",
        },
    )
    assert res.status_code == 403
