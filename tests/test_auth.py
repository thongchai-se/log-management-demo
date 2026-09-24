"""Unit tests: authentication and tenant authorization helpers."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.deps import get_current_user, require_admin, resolve_tenant


class _Creds:
    def __init__(self, token: str):
        self.credentials = token


def test_resolve_tenant_viewer_forced():
    viewer = {"username": "viewer", "role": "viewer", "tenant": "demoA"}
    assert resolve_tenant(viewer, "demoB") == "demoA"
    assert resolve_tenant(viewer, None) == "demoA"


def test_resolve_tenant_admin_optional_filter():
    admin = {"username": "admin", "role": "admin", "tenant": None}
    assert resolve_tenant(admin, "demoB") == "demoB"
    assert resolve_tenant(admin, None) is None


def test_get_current_user_valid_admin():
    user = get_current_user(_Creds("demo-token-admin"))  # type: ignore[arg-type]
    assert user["username"] == "admin"
    assert user["role"] == "admin"
    assert user["tenant"] is None


def test_get_current_user_valid_viewer():
    user = get_current_user(_Creds("demo-token-viewer"))  # type: ignore[arg-type]
    assert user["role"] == "viewer"
    assert user["tenant"] == "demoA"


def test_get_current_user_rejects_bad_prefix():
    with pytest.raises(HTTPException) as exc:
        get_current_user(_Creds("bearer-admin"))  # type: ignore[arg-type]
    assert exc.value.status_code == 401


def test_get_current_user_rejects_unknown_user():
    with pytest.raises(HTTPException) as exc:
        get_current_user(_Creds("demo-token-nobody"))  # type: ignore[arg-type]
    assert exc.value.status_code == 401


def test_require_admin_allows_admin():
    admin = {"username": "admin", "role": "admin", "tenant": None}
    assert require_admin(admin) == admin


def test_require_admin_blocks_viewer():
    viewer = {"username": "viewer", "role": "viewer", "tenant": "demoA"}
    with pytest.raises(HTTPException) as exc:
        require_admin(viewer)
    assert exc.value.status_code == 403
