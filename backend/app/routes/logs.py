from fastapi import APIRouter, Query, Depends
from app.services.search import search_logs
from app.deps import get_current_user, resolve_tenant

router = APIRouter()


@router.get("/logs")
def get_logs(
    tenant: str | None = Query(default=None),
    source: str | None = Query(default=None),
    time_from: str | None = Query(default=None, alias="from"),
    time_to: str | None = Query(default=None, alias="to"),
    event_type: str | None = Query(default=None),
    user: str | None = Query(default=None),
    size: int = Query(default=50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    effective_tenant = resolve_tenant(current_user, tenant)
    return search_logs(
        tenant=effective_tenant,
        source=source,
        event_type=event_type,
        user=user,
        time_from=time_from,
        time_to=time_to,
        size=size,
    )
