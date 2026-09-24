from datetime import datetime, timedelta, timezone

from app.config import LOG_INDEX, RETENTION_DAYS
from app.database.opensearch import client


def _text_keyword() -> dict:
    """text field with .keyword subfield for aggregations and exact filters."""
    return {
        "type": "text",
        "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
    }


MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "index.mapping.total_fields.limit": 2000,
    },
    "mappings": {
        "properties": {
            "@timestamp": {"type": "date"},
            "tenant": _text_keyword(),
            "source": _text_keyword(),
            "vendor": _text_keyword(),
            "product": _text_keyword(),
            "event_type": _text_keyword(),
            "event_subtype": _text_keyword(),
            "severity": {"type": "integer"},
            "action": _text_keyword(),
            "src_ip": _text_keyword(),
            "src_port": {"type": "integer"},
            "dst_ip": _text_keyword(),
            "dst_port": {"type": "integer"},
            "protocol": _text_keyword(),
            "user": _text_keyword(),
            "host": _text_keyword(),
            "process": _text_keyword(),
            "url": _text_keyword(),
            "http_method": _text_keyword(),
            "status_code": {"type": "integer"},
            "rule_name": _text_keyword(),
            "rule_id": _text_keyword(),
            "cloud": {
                "properties": {
                    "account_id": {"type": "keyword"},
                    "region": {"type": "keyword"},
                    "service": {"type": "keyword"},
                }
            },
            "raw": {"type": "object", "enabled": True},
            "_tags": {"type": "keyword"},
        }
    },
}


def ensure_index() -> None:
    if client.indices.exists(index=LOG_INDEX):
        return
    client.indices.create(index=LOG_INDEX, body=MAPPING)
    print(f"[index] created {LOG_INDEX}")


def purge_old_logs() -> dict:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()
    body = {"query": {"range": {"@timestamp": {"lt": cutoff}}}}
    res = client.delete_by_query(index=LOG_INDEX, body=body, refresh=True, conflicts="proceed")
    deleted = res.get("deleted", 0)
    print(f"[retention] deleted={deleted} cutoff={cutoff}")
    return {
        "deleted": deleted,
        "cutoff": cutoff,
        "retention_days": RETENTION_DAYS,
    }
