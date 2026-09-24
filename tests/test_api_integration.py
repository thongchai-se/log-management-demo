"""Integration tests against OpenSearch (skipped when cluster is down)."""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SAMPLE = Path(__file__).resolve().parents[1] / "sample"


def _opensearch_up() -> bool:
    try:
        from app.database.opensearch import client

        return bool(client.ping())
    except Exception:
        return False


requires_opensearch = pytest.mark.skipif(
    not _opensearch_up(),
    reason="OpenSearch not reachable on localhost:9200",
)


@requires_opensearch
def test_ingest_search_dashboard_roundtrip(api_client, admin_headers):
    from app.services.index_setup import ensure_index

    ensure_index()
    marker = f"pytest_roundtrip_{datetime.now(timezone.utc).strftime('%H%M%S%f')}"

    ingest = api_client.post(
        "/api/ingest",
        headers=admin_headers,
        json={
            "tenant": "demoA",
            "source": "api",
            "event_type": marker,
            "user": "tester",
            "ip": "198.51.100.9",
            "severity": 3,
        },
    )
    assert ingest.status_code == 200
    assert ingest.json()["status"] == "accepted"

    logs = api_client.get(
        f"/api/logs?tenant=demoA&source=api&size=50",
        headers=admin_headers,
    )
    assert logs.status_code == 200
    body = logs.json()
    assert body["total"] >= 1
    assert any(row.get("event_type") == marker for row in body["logs"])

    dash = api_client.get("/api/dashboard?tenant=demoA", headers=admin_headers)
    assert dash.status_code == 200
    stats = dash.json()
    assert stats["total_logs"] >= 1
    assert "top_ip" in stats
    assert "top_user" in stats
    assert "by_event_type" in stats
    assert "timeline" in stats


@requires_opensearch
def test_viewer_cannot_read_other_tenant(api_client, admin_headers, viewer_headers):
    secret = f"secret_b_{datetime.now(timezone.utc).strftime('%H%M%S%f')}"
    api_client.post(
        "/api/ingest",
        headers=admin_headers,
        json={
            "tenant": "demoB",
            "source": "api",
            "event_type": secret,
            "user": "bob",
            "ip": "198.51.100.50",
        },
    )

    # Viewer requests demoB explicitly — backend must force demoA
    res = api_client.get(
        "/api/logs?tenant=demoB&size=100",
        headers=viewer_headers,
    )
    assert res.status_code == 200
    for row in res.json()["logs"]:
        assert row.get("tenant") == "demoA"
        assert row.get("event_type") != secret


@requires_opensearch
def test_batch_upload_sample_files(api_client, admin_headers):
    files = []
    for name in ("aws_cloudtrail.json", "m365_audit.json", "ad_4625.json", "crowdstrike_malware.json"):
        path = SAMPLE / name
        files.append(("files", (name, path.read_bytes(), "application/json")))

    res = api_client.post(
        "/api/ingest/batch",
        headers=admin_headers,
        files=files,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["accepted"] >= 4
    assert body["failed"] == 0


@requires_opensearch
def test_alert_login_failed_same_ip(api_client, admin_headers):
    now = datetime.now(timezone.utc)
    ip = "203.0.113.200"
    for i in range(4):
        ts = (now - timedelta(seconds=10 * i)).isoformat()
        res = api_client.post(
            "/api/ingest",
            headers=admin_headers,
            json={
                "tenant": "demoA",
                "source": "api",
                "event_type": "app_login_failed",
                "user": "alice",
                "ip": ip,
                "action": "login_failed",
                "severity": 6,
                "@timestamp": ts,
            },
        )
        assert res.status_code == 200, res.text

    alerts = api_client.get(
        "/api/alerts?window_minutes=5&min_count=3&tenant=demoA",
        headers=admin_headers,
    )
    assert alerts.status_code == 200
    payload = alerts.json()
    assert payload["total"] >= 1
    assert any(a.get("src_ip") == ip and a.get("count", 0) >= 3 for a in payload["alerts"])


@requires_opensearch
def test_admin_retention_endpoints(api_client, admin_headers):
    info = api_client.get("/api/admin/retention", headers=admin_headers)
    assert info.status_code == 200
    assert info.json()["retention_days"] == 7

    purge = api_client.post("/api/admin/retention/purge", headers=admin_headers)
    assert purge.status_code == 200
    assert "deleted" in purge.json()


@requires_opensearch
def test_filter_by_source_and_time(api_client, admin_headers):
    ts = datetime.now(timezone.utc).isoformat()
    marker = f"filter_src_{datetime.now(timezone.utc).strftime('%H%M%S%f')}"
    api_client.post(
        "/api/ingest",
        headers=admin_headers,
        json={
            "tenant": "demoA",
            "source": "crowdstrike",
            "event_type": marker,
            "host": "WIN10-01",
            "severity": 8,
            "@timestamp": ts,
        },
    )

    res = api_client.get(
        f"/api/logs?tenant=demoA&source=crowdstrike&size=50",
        headers=admin_headers,
    )
    assert res.status_code == 200
    rows = res.json()["logs"]
    assert any(r.get("event_type") == marker for r in rows)
    assert all(r.get("source") == "crowdstrike" for r in rows if r.get("event_type") == marker)


@requires_opensearch
def test_ingest_rejects_invalid_json_batch(api_client, admin_headers):
    bad = io.BytesIO(b"not-json")
    res = api_client.post(
        "/api/ingest/batch",
        headers=admin_headers,
        files=[("files", ("bad.json", bad, "application/json"))],
    )
    # FastAPI / handler should surface an error (400/500) rather than accepting
    assert res.status_code >= 400
