"""Seed >=3 recent login failures from the same IP so /api/alerts lights up."""

from datetime import datetime, timedelta, timezone
import requests

API_URL = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "admin123"
IP = "203.0.113.77"


def login() -> str:
    res = requests.post(
        f"{API_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
        timeout=10,
    )
    res.raise_for_status()
    return res.json()["access_token"]


def main() -> None:
    token = login()
    now = datetime.now(timezone.utc)
    for i in range(4):
        ts = (now - timedelta(seconds=30 * i)).isoformat()
        payload = {
            "tenant": "demoA",
            "source": "api",
            "event_type": "app_login_failed",
            "user": "alice",
            "ip": IP,
            "reason": "wrong_password",
            "@timestamp": ts,
            "severity": 6,
            "action": "login_failed",
        }
        res = requests.post(
            f"{API_URL}/api/ingest",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=10,
        )
        print(i + 1, res.status_code, res.json() if res.ok else res.text)

    alerts = requests.get(
        f"{API_URL}/api/alerts?window_minutes=5&min_count=3",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    print("alerts:", alerts.status_code, alerts.text[:500])


if __name__ == "__main__":
    main()
