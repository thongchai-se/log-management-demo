from fastapi import APIRouter, Depends

from app.config import RETENTION_DAYS
from app.deps import require_admin
from app.services.index_setup import ensure_index, purge_old_logs

router = APIRouter(prefix="/admin")


@router.post("/retention/purge")
def run_purge(current_user: dict = Depends(require_admin)):
    result = purge_old_logs()
    result["requested_by"] = current_user["username"]
    return result


@router.get("/retention")
def retention_info(current_user: dict = Depends(require_admin)):
    return {
        "retention_days": RETENTION_DAYS,
        "policy": "delete_by_query on @timestamp older than retention_days",
        "requested_by": current_user["username"],
    }


@router.post("/index/ensure")
def ensure(current_user: dict = Depends(require_admin)):
    ensure_index()
    return {"status": "ok", "requested_by": current_user["username"]}
