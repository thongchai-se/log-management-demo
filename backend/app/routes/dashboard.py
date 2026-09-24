from fastapi import APIRouter, Query, Depends
from app.services.search import get_dashboard_stats
from app.deps import get_current_user, resolve_tenant

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(
    tenant: str | None = Query(default=None),
    source: str | None = Query(default=None),
    time_from: str | None = Query(default=None, alias="from"),
    time_to: str | None = Query(default=None, alias="to"),
    current_user: dict = Depends(get_current_user),
):
    effective_tenant = resolve_tenant(current_user, tenant)
    return get_dashboard_stats(
        tenant=effective_tenant,
        source=source,
        time_from=time_from,
        time_to=time_to,
    )
