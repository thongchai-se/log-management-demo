from fastapi import APIRouter, Query, Depends
from app.services.search import get_alerts
from app.deps import get_current_user

router = APIRouter()


@router.get("/alerts")
def get_alerts_route(
    tenant: str | None = Query(default=None),
    min_severity: int = Query(default=3, ge=0, le=10),
    current_user: str = Depends(get_current_user),
):
    return get_alerts(tenant=tenant, min_severity=min_severity)