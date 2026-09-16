from fastapi import APIRouter, Query , Depends
from app.services.search import search_logs
from app.deps import get_current_user

router = APIRouter()

@router.get("/logs")
def get_logs(
    tenant: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    user: str | None = Query(default=None),
    size: int = Query(default=50, ge=1, le=100),
    current_user: str = Depends(get_current_user),
):
    return search_logs(
        tenant=tenant,
        event_type=event_type,
        user=user,
        size=size,
    )