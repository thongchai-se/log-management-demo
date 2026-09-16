from app.database.opensearch import client
from app.config import LOG_INDEX
from app.services.normalization import normalize_api_log

def ingest_log_document(payload: dict) -> dict:
    """
    รับ dict ของ log → normalize → เก็บลง OpenSearch
    คืนค่าเป็นผลลัพธ์สั้นๆ ให้ route เอาไปตอบ
    """
    normalized = normalize_api_log(payload)

    response = client.index(
        index=LOG_INDEX,
        body=normalized,
    )

    return {
        "status": "accepted",
        "id": response["_id"],
    }