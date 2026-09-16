from app.database.opensearch import client
from app.config import LOG_INDEX


def search_logs(
    tenant: str | None = None,
    event_type: str | None = None,
    user: str | None = None,
    size: int = 50,
) -> dict: 
    filters = []

    if tenant:
        filters.append({"term": {"tenant.keyword": tenant}})
    if event_type:
        filters.append({"term": {"event_type.keyword": event_type}})
    if user:
        filters.append({"term": {"user.keyword": user}})

    if filters:
        query = {"bool": {"filter": filters}}
    else:
        query = {"match_all": {}}

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

def get_dashboard_stats(tenant: str | None = None) -> dict:
    if tenant:
        query = {
            "bool": {
                "filter": [{"term": {"tenant.keyword": tenant}}],
            }
        } 
    else: 
        query = {"match_all": {}}

    response = client.search(
        index=LOG_INDEX,
        body={
            "size": 0,
            "query": query,
            "aggs": {
                "by_severity": {
                    "terms": {"field": "severity", "size": 10,}
                },
                "by_event_type": {
                    "terms": {"field": "event_type.keyword", "size": 10,}
                },
            },
        },
    )
    
    severity_buckets = response["aggregations"]["by_severity"]["buckets"]
    event_type_buckets = response["aggregations"]["by_event_type"]["buckets"]

    return {
        "total_logs": response["hits"]["total"]["value"],
        "by_severity": [
            {"key": b["key"], "count": b["doc_count"]}
            for b in severity_buckets
        ],
        "by_event_type": [
            {"key": b["key"], "count": b["doc_count"]}
            for b in event_type_buckets
        ],
    }

def get_alerts(
    tenant: str | None = None,
    min_severity: int = 3,
) -> dict:
    filters = [
        {"range": {"severity": {"gte": min_severity}}},
    ]

    if tenant:
        filters.append({"term": {"tenant.keyword": tenant}})

    response = client.search(
        index=LOG_INDEX,
        body={
            "query": {"bool": {"filter": filters}},
            "size": 20,
            "sort": [
                {"@timestamp": {"order": "desc"}}
            ],
        },
    )

    alerts = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        alerts.append({
            "id": hit["_id"],
            "timestamp": source.get("@timestamp"),
            "tenant": source.get("tenant"),
            "severity": source.get("severity"),
            "event_type": source.get("event_type"),
            "user": source.get("user"),
            "src_ip": source.get("src_ip"),
            "action": source.get("action"),
        })

    return {
        "total": response["hits"]["total"]["value"],
        "min_severity": min_severity,
        "alerts": alerts,
    }