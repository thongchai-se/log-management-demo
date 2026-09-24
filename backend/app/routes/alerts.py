from fastapi import APIRouter, Depends, Query

from app.deps import get_current_user, resolve_tenant
from app.services.search import get_alerts

router = APIRouter()


@router.get("/alerts")
def get_alerts_route(
    tenant: str | None = Query(default=None),
    window_minutes: int = Query(default=5, ge=1, le=60),
    min_count: int = Query(default=3, ge=1, le=50),
    notify: bool = Query(default=False),
    current_user: dict = Depends(get_current_user),
):
    effective_tenant = resolve_tenant(current_user, tenant)
    return get_alerts(
        tenant=effective_tenant,
        window_minutes=window_minutes,
        min_count=min_count,
        notify=notify,
    )
