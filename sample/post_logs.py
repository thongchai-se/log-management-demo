from datetime import datetime, timezone
from pathlib import Path
import json
import requests

API_URL = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "admin123"
SAMPLE_DIR = Path(__file__).resolve().parent


def login() -> str:
    res = requests.post(
        f"{API_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
        timeout=10,
    )
    res.raise_for_status()
    return res.json()["access_token"]


def post_one(token: str, path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    res = requests.post(
        f"{API_URL}/api/ingest",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=10,
    )
    if res.ok:
        data = res.json()
        print(f"OK  {path.name} -> source={data.get('source')} id={data.get('id')}")
    else:
        print(f"FAIL {path.name} -> {res.status_code} {res.text}")


def main() -> None:
    token = login()
    files = sorted(SAMPLE_DIR.glob("*.json"))
    print(f"found {len(files)} files")
    for path in files:
        post_one(token, path)


if __name__ == "__main__":
    main()
