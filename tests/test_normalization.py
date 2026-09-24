"""Unit tests: schema normalization for every supported source."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.normalization import normalize_log, parse_syslog_message

SAMPLE = Path(__file__).resolve().parents[1] / "sample"


def test_normalize_api_maps_ip_to_src_ip():
    doc = normalize_log(
        {
            "tenant": "demoA",
            "source": "api",
            "event_type": "app_login_failed",
            "user": "alice",
            "ip": "203.0.113.7",
            "reason": "wrong_password",
            "@timestamp": "2025-08-20T07:20:00Z",
        }
    )
    assert doc["source"] == "api"
    assert doc["tenant"] == "demoA"
    assert doc["src_ip"] == "203.0.113.7"
    assert doc["event_type"] == "app_login_failed"
    assert doc["@timestamp"] == "2025-08-20T07:20:00Z"
    assert "raw" in doc


def test_normalize_crowdstrike_defaults_and_sha_tag():
    doc = normalize_log(
        {
            "tenant": "demoA",
            "source": "crowdstrike",
            "event_type": "malware_detected",
            "host": "WIN10-01",
            "process": "powershell.exe",
            "sha256": "abc123",
            "action": "quarantine",
        }
    )
    assert doc["source"] == "crowdstrike"
    assert doc["vendor"] == "crowdstrike"
    assert doc["product"] == "falcon"
    assert doc["severity"] == 8
    assert "sha256:abc123" in doc["_tags"]


def test_normalize_aws_cloud_fields():
    doc = normalize_log(
        {
            "tenant": "demoB",
            "source": "aws",
            "event_type": "CreateUser",
            "user": "admin",
            "cloud": {
                "service": "iam",
                "account_id": "123456789012",
                "region": "ap-southeast-1",
            },
        }
    )
    assert doc["source"] == "aws"
    assert doc["vendor"] == "aws"
    assert doc["cloud"]["account_id"] == "123456789012"
    assert doc["cloud"]["region"] == "ap-southeast-1"


def test_normalize_m365_maps_status_to_action():
    doc = normalize_log(
        {
            "tenant": "demoB",
            "source": "m365",
            "event_type": "UserLoggedIn",
            "user": "bob@demo.local",
            "ip": "198.51.100.23",
            "status": "Success",
        }
    )
    assert doc["source"] == "m365"
    assert doc["vendor"] == "microsoft"
    assert doc["product"] == "m365"
    assert doc["src_ip"] == "198.51.100.23"
    assert doc["action"] == "success"


def test_normalize_ad_4625():
    doc = normalize_log(
        {
            "tenant": "demoA",
            "source": "ad",
            "event_id": 4625,
            "event_type": "LogonFailed",
            "user": r"demo\eve",
            "host": "DC01",
            "ip": "203.0.113.77",
            "logon_type": 3,
        }
    )
    assert doc["source"] == "ad"
    assert doc["severity"] == 6
    assert doc["rule_id"] == "4625"
    assert doc["action"] == "login"
    assert "event_id:4625" in doc["_tags"]
    assert doc["src_ip"] == "203.0.113.77"


def test_normalize_firewall_and_network_preserve_source():
    fw = normalize_log(
        {
            "tenant": "demoA",
            "source": "firewall",
            "action": "deny",
            "src_ip": "10.0.1.10",
            "dst_ip": "8.8.8.8",
        }
    )
    assert fw["source"] == "firewall"
    assert fw["product"] == "ngfw"

    net = normalize_log(
        {
            "tenant": "demoA",
            "source": "network",
            "event_type": "link-down",
            "host": "r1",
        }
    )
    assert net["source"] == "network"
    assert net["product"] == "router"


def test_normalize_unknown_source_gets_tag():
    doc = normalize_log({"tenant": "demoA", "source": "custom_sensor", "event_type": "x"})
    assert doc["source"] == "custom_sensor"
    assert "unknown_source" in doc["_tags"]


def test_normalize_default_source_is_api():
    doc = normalize_log({"tenant": "demoA", "event_type": "ping"})
    assert doc["source"] == "api"


def test_parse_syslog_firewall_assignment_sample():
    raw = (
        "<134>Aug 20 12:44:56 fw01 vendor=demo product=ngfw "
        "action=deny src=10.0.1.10 dst=8.8.8.8 spt=5353 dpt=53 "
        "proto=udp msg=DNS_blocked policy=Block-DNS"
    )
    parsed = parse_syslog_message(raw, tenant="demoA")
    assert parsed["source"] == "firewall"
    assert parsed["src_ip"] == "10.0.1.10"
    assert parsed["dst_ip"] == "8.8.8.8"
    assert parsed["src_port"] == 5353
    assert parsed["dst_port"] == 53
    assert parsed["protocol"] == "udp"
    assert parsed["action"] == "deny"
    assert parsed["severity"] == 5
    assert parsed["rule_name"] == "Block-DNS"

    doc = normalize_log(parsed)
    assert doc["source"] == "firewall"
    assert doc["rule_name"] == "Block-DNS"


def test_parse_syslog_network_link_down():
    raw = (
        "<190>Aug 20 13:01:02 r1 if=ge-0/0/1 event=link-down "
        "mac=aa:bb:cc:dd:ee:ff reason=carrier-loss"
    )
    parsed = parse_syslog_message(raw, tenant="demoA")
    assert parsed["event_type"] == "link-down"
    assert "syslog" in parsed["_tags"]


def test_sample_json_files_normalize_cleanly():
    """Every committed sample/*.json must normalize without raising."""
    files = sorted(SAMPLE.glob("*.json"))
    assert files, "expected sample JSON fixtures"
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            doc = normalize_log(item)
            assert doc.get("source")
            assert doc.get("tenant")
            assert "@timestamp" in doc
