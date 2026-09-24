from fastapi import APIRouter, HTTPException, status
from app.config import DEMO_USER
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest):
    user = DEMO_USER.get(body.username)

    if user is None or user["password"] != body.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = f"demo-token-{body.username}"

    return {
        "access_token": token,
        "token_type": "Bearer",
        "username": body.username,
        "role": user["role"],
        "tenant": user["tenant"],
    }
