from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import DEMO_USER

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    prefix = "demo-token-"

    if not token.startswith(prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    username = token.removeprefix(prefix)
    user = DEMO_USER.get(username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return {
        "username": username,
        "role": user["role"],
        "tenant": user["tenant"],
    }


def resolve_tenant(current_user: dict, requested: str | None) -> str | None:
    """Viewer is scoped to their own tenant; admin may filter optionally."""
    if current_user.get("role") == "viewer":
        return current_user.get("tenant")
    return requested


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user
