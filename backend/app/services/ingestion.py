from app.config import LOG_INDEX
from app.database.opensearch import client
from app.services.index_setup import ensure_index
from app.services.normalization import normalize_log


def ingest_log_document(payload: dict) -> dict:
    ensure_index()
    normalized = normalize_log(payload)

    response = client.index(
        index=LOG_INDEX,
        body=normalized,
        refresh=True,
    )

    return {
        "status": "accepted",
        "id": response["_id"],
        "source": normalized.get("source"),
        "tenant": normalized.get("tenant"),
    }


def ingest_many(payloads: list[dict]) -> dict:
    accepted = []
    failed = []

    for i, payload in enumerate(payloads):
        try:
            result = ingest_log_document(payload)
            accepted.append(result)
        except Exception as e:
            failed.append({"index": i, "error": str(e)})

    return {
        "accepted": len(accepted),
        "failed": len(failed),
        "items": accepted,
        "errors": failed,
    }
