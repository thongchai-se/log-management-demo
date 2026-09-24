"""Shared pytest fixtures for Log Management Demo."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SAMPLE = ROOT / "sample"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Avoid clashing with a running local uvicorn syslog listener during tests
os.environ.setdefault("SYSLOG_PORT", "15514")


def opensearch_available() -> bool:
    try:
        from app.database.opensearch import client

        return bool(client.ping())
    except Exception:
        return False


@pytest.fixture(scope="session")
def sample_dir() -> Path:
    return SAMPLE


@pytest.fixture(scope="session")
def api_client():
    """One TestClient for the whole session (single lifespan / syslog bind)."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        yield client


def login(client, username: str, password: str) -> dict:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def admin_headers(api_client):
    data = login(api_client, "admin", "admin123")
    return auth_header(data["access_token"])


@pytest.fixture(scope="session")
def viewer_headers(api_client):
    data = login(api_client, "viewer", "viewer123")
    return auth_header(data["access_token"])
