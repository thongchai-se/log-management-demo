from datetime import datetime, timezone
import re

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base(data: dict, source: str) -> dict:
    """Build the common normalized fields."""
    ts = data.get("@timestamp") or data.get("timestamp") or _now()
    return {
        "@timestamp": ts,
        "tenant": data.get("tenant", "default"),
        "source": source,
        "vendor": data.get("vendor"),
        "product": data.get("product"),
        "event_type": data.get("event_type"),
        "event_subtype": data.get("event_subtype"),
        "severity": data.get("severity", 0),
        "action": data.get("action"),
        "src_ip": data.get("src_ip") or data.get("ip"),
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
        "_tags": data.get("_tags", []),
    }


def normalize_api_log(data: dict) -> dict:
    doc = _base(data, "api")
    return doc


def normalize_crowdstrike_log(data: dict) -> dict:
    doc = _base(data, "crowdstrike")
    doc["vendor"] = data.get("vendor", "crowdstrike")
    doc["product"] = data.get("product", "falcon")
    if not doc["severity"]:
        doc["severity"] = 8
    
    if data.get("sha256"):
        doc["_tags"] = list(doc["_tags"]) + [f"sha256:{data['sha256']}"]
    return doc


def normalize_aws_log(data: dict) -> dict:
    doc = _base(data, "aws")
    doc["vendor"] = data.get("vendor", "aws")
    doc["cloud"] = data.get("cloud", {})
    return doc
    

def normalize_m365_log(data: dict) -> dict:
    doc = _base(data, "m365")
    doc["vendor"] = data.get("vendor", "microsoft")
    doc["product"] = data.get("product", "m365")
    status = data.get("status")
    if status and not doc["action"]:
        doc["action"] = str(status).lower()
    return doc


def normalize_ad_log(data: dict) -> dict:
    doc = _base(data, "ad")
    doc["vendor"] = data.get("vendor", "microsoft")
    doc["product"] = data.get("product", "active_directory")
    if data.get("event_id") is not None:
        doc["rule_id"] = str(data["event_id"])
        doc["_tags"] = list(doc["_tags"]) + [f"event_id:{data['event_id']}"]
    if data.get("event_id") == 4625 and not data.get("severity"):
        doc["severity"] = 6
        if not doc["action"]:
            doc["action"] = "login"
    return doc


def parse_syslog_message(message: str, tenant: str = "demoA") -> dict:
    text = message.strip()

    text = re.sub(r"^<\d+>", "", text).strip()

    fields = dict(re.findall(r"(\w+)=([^\s]+)", text))

    parts = text.split()
    host = parts[3] if len(parts) >= 4 else None

    return {
        "tenant": tenant,
        "source": "firewall",
        "vendor": fields.get("vendor"),
        "product": fields.get("product"),
        "action": fields.get("action"),
        "src_ip": fields.get("src"),
        "dst_ip": fields.get("dst"),
        "src_port": int(fields["spt"]) if fields.get("spt", "").isdigit() else None,
        "dst_port": int(fields["dpt"]) if fields.get("dpt", "").isdigit() else None,
        "protocol": fields.get("proto"),
        "host": host,
        "rule_name": fields.get("policy") or fields.get("msg"),
        "event_type": fields.get("event") or fields.get("action") or "syslog",
        "severity": 5 if fields.get("action") == "deny" else 2,
        "raw": {"message": message},
        "_tags": ["syslog"],
    }


def normalized_firewall_log(data: dict) -> dict:
    source = (data.get("source") or "firewall").lower()
    if source not in ("firewall", "network"):
        source = "firewall"
    doc = _base(data, source)
    doc["vendor"] = data.get("vendor", "demo")
    doc["product"] = data.get("product", "ngfw" if source == "firewall" else "router")
    return doc

def normalize_log(data: dict) -> dict:
    source = (data.get("source") or "api").lower()
    if source == "api":
        return normalize_api_log(data)
    if source == "crowdstrike":
        return normalize_crowdstrike_log(data)
    if source == "aws":
        return normalize_aws_log(data)
    if source == "m365":
        return normalize_m365_log(data)
    if source == "ad":
        return normalize_ad_log(data)
    if source in ("firewall", "network"):
        return normalized_firewall_log(data)
    doc = _base(data, source)
    doc["_tags"] = list(doc["_tags"]) + ["unknown_source"]
    return doc