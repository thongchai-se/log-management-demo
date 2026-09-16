from fastapi import APIRouter, Depends, Query
from app.schemas.log import LogIngestRequest
from app.services.ingestion import ingest_log_document
from app.deps import get_current_user

router = APIRouter()


@router.post("/ingest")
def ingest_log(log: LogIngestRequest, current_user: str = Depends(get_current_user),):
    payload = log.model_dump(by_alias=True)
    return ingest_log_document(payload)
