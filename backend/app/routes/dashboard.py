from fastapi import APIRouter, Query, Depends
from app.services.search import get_dashboard_stats
from app.deps import get_current_user

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(tenant: str | None = Query(default=None), current_user: str = Depends(get_current_user)):
    return get_dashboard_stats(tenant=tenant)
