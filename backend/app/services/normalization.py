from datetime import datetime, timezone



def normalize_api_log(data: dict) -> dict:

    return {
        "@timestamp": data.get(
            "@timestamp",
            datetime.now(timezone.utc).isoformat()
        ),

        "tenant": data.get("tenant", "default"),

        "source": "api",

        "vendor": data.get("vendor"),

        "product": data.get("product"),

        "event_type": data.get("event_type"),

        "event_subtype": data.get("event_subtype"),

        "severity": data.get("severity", 0),

        "action": data.get("action"),

        "src_ip": data.get("ip"),

        "src_port": data.get("src_port"),

        "dst_ip": data.get("dst_ip"),

        "dst_port": data.get("dst_port"),

        "protocol": data.get("protocol"),

        "user": data.get("user"),

        "host": data.get("host"),

        "process": data.get("process"),

        "url": data.get("url"),

        "http_method": data.get("http_method"),

        "status_code": data.get("status_code"),

        "rule_name": data.get("rule_name"),

        "rule_id": data.get("rule_id"),

        "cloud": data.get("cloud", {}),

        "raw": data,

        "_tags": data.get("_tags", [])
    }