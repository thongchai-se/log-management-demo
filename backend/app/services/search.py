from datetime import datetime, timedelta, timezone

import requests

from app.config import ALERT_WEBHOOK_URL, LOG_INDEX
from app.database.opensearch import client


def _term(field: str, value: str) -> dict:
    # Support both explicit keyword mapping and dynamic text+.keyword
    return {
        "bool": {
            "should": [
                {"term": {field: value}},
                {"term": {f"{field}.keyword": value}},
            ],
            "minimum_should_match": 1,
        }
    }

def search_logs(
    tenant: str | None = None,
    source: str | None = None,
    event_type: str | None = None,
    user: str | None = None,
    time_from: str | None = None,
    time_to: str | None = None,
    size: int = 50,
) -> dict:
    filters = []

    if tenant:
        filters.append(_term("tenant", tenant))
    if source:
        filters.append(_term("source", source))
    if event_type:
        filters.append(_term("event_type", event_type))
    if user:
        filters.append(_term("user", user))

    if time_from or time_to:
        rng: dict = {}
        if time_from:
            rng["gte"] = time_from
        if time_to:
            rng["lte"] = time_to
        filters.append({"range": {"@timestamp": rng}})

    query = {"bool": {"filter": filters}} if filters else {"match_all": {}}

    response = client.search(
        index=LOG_INDEX,
        body={
            "query": query,
            "size": size,
            "sort": [{"@timestamp": {"order": "desc"}}],
        },
    )

    logs = []
    for hit in response["hits"]["hits"]:
        item = {"id": hit["_id"]}
        item.update(hit["_source"])
        logs.append(item)

    return {
        "total": response["hits"]["total"]["value"],
        "logs": logs,
    }


def get_dashboard_stats(
    tenant: str | None = None,
    source: str | None = None,
    time_from: str | None = None,
    time_to: str | None = None,
) -> dict:
    filters = []

    if tenant:
        filters.append(_term("tenant", tenant))
    if source:
        filters.append(_term("source", source))

    if time_from or time_to:
        rng = {}
        if time_from:
            rng["gte"] = time_from
        if time_to:
            rng["lte"] = time_to
        filters.append({"range": {"@timestamp": rng}})

    query = {"bool": {"filter": filters}} if filters else {"match_all": {}}

    response = client.search(
        index=LOG_INDEX,
        body={
            "size": 0,
            "query": query,
            "aggs": {
                "by_severity": {"terms": {"field": "severity", "size": 10}},
                "by_event_type": {"terms": {"field": "event_type.keyword", "size": 10}},
                "top_ip": {"terms": {"field": "src_ip.keyword", "size": 10}},
                "top_user": {"terms": {"field": "user.keyword", "size": 10}},
                "timeline": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "calendar_interval": "hour",
                        "min_doc_count": 0,
                    }
                },
            },
        },
    )

    aggs = response["aggregations"]

    def buckets(name: str):
        return [
            {"key": b["key"], "count": b["doc_count"]}
            for b in aggs[name]["buckets"]
            if b.get("key") not in (None, "")
        ]

    timeline = [
        {
            "key": b.get("key_as_string", str(b["key"])),
            "count": b["doc_count"],
        }
        for b in aggs["timeline"]["buckets"]
    ]

    return {
        "total_logs": response["hits"]["total"]["value"],
        "by_severity": buckets("by_severity"),
        "by_event_type": buckets("by_event_type"),
        "top_ip": buckets("top_ip"),
        "top_user": buckets("top_user"),
        "timeline": timeline,
    }


def _notify_webhook(alerts_payload: dict) -> None:
    if not ALERT_WEBHOOK_URL or not alerts_payload.get("alerts"):
        return
    try:
        requests.post(ALERT_WEBHOOK_URL, json=alerts_payload, timeout=5)
    except Exception as exc:
        print(f"[alert-webhook] error: {exc}")


def get_alerts(
    tenant: str | None = None,
    window_minutes: int = 5,
    min_count: int = 3,
    notify: bool = False,
) -> dict:
    now = datetime.now(timezone.utc)
    since = (now - timedelta(minutes=window_minutes)).isoformat()
    filters = [
        {"range": {"@timestamp": {"gte": since}}},
        {
            "bool": {
                "should": [
                    _term("event_type", "app_login_failed"),
                    _term("event_type", "LogonFailed"),
                    _term("action", "login_failed"),
                ],
                "minimum_should_match": 1,
            }
        },
    ]
    if tenant:
        filters.append(_term("tenant", tenant))

    response = client.search(
        index=LOG_INDEX,
        body={
            "size": 0,
            "query": {"bool": {"filter": filters}},
            "aggs": {
                "by_ip": {
                    "terms": {"field": "src_ip.keyword", "size": 20},
                    "aggs": {
                        "samples": {
                            "top_hits": {
                                "size": 3,
                                "sort": [{"@timestamp": {"order": "desc"}}],
                            }
                        }
                    },
                }
            },
        },
    )

    alerts = []
    for b in response["aggregations"]["by_ip"]["buckets"]:
        if b["doc_count"] < min_count:
            continue
        hits = b["samples"]["hits"]["hits"]
        src = hits[0]["_source"] if hits else {}
        alerts.append(
            {
                "id": f"brute-{b['key']}",
                "rule": "login_failed_same_ip",
                "timestamp": src.get("@timestamp"),
                "tenant": src.get("tenant"),
                "severity": 8,
                "event_type": src.get("event_type"),
                "user": src.get("user"),
                "src_ip": b["key"],
                "action": src.get("action"),
                "count": b["doc_count"],
                "window_minutes": window_minutes,
            }
        )

    payload = {
        "total": len(alerts),
        "rule": "login_failed_same_ip",
        "window_minutes": window_minutes,
        "min_count": min_count,
        "alerts": alerts,
    }
    if notify:
        _notify_webhook(payload)
    return payload
