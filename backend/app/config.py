import os

OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))
LOG_INDEX = os.getenv("LOG_INDEX", "logs")
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "7"))
SYSLOG_HOST = os.getenv("SYSLOG_HOST", "0.0.0.0")
SYSLOG_PORT = int(os.getenv("SYSLOG_PORT", "5514"))
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "").strip()
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost,https://localhost",
    ).split(",")
    if o.strip()
]

DEMO_USER = {
    "admin": {"password": "admin123", "role": "admin", "tenant": None},
    "viewer": {"password": "viewer123", "role": "viewer", "tenant": "demoA"},
}
