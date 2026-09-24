from typing import Annotated
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
import json

from app.schemas.log import LogIngestRequest
from app.services.ingestion import ingest_log_document, ingest_many
from app.deps import require_admin

router = APIRouter()


@router.post("/ingest")
def ingest_log(
    log: LogIngestRequest,
    current_user: dict = Depends(require_admin),
):
    payload = log.model_dump(by_alias=True)
    return ingest_log_document(payload)


@router.post("/ingest/batch")
async def ingest_batch(
    files: Annotated[list[UploadFile], File(description="JSON log files")],
    current_user: dict = Depends(require_admin),
):
    payloads = []

    for f in files:
        content = await f.read()
        try:
            text = content.decode("utf-8")
            data = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON in file {f.filename}: {exc}",
            ) from exc

        if isinstance(data, list):
            payloads.extend(data)
        else:
            payloads.append(data)

    return ingest_many(payloads)
