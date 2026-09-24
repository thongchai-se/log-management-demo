"""
Test suite overview
-------------------
Unit (no OpenSearch):
  - test_normalization.py  — schema mapping every source + sample fixtures
  - test_auth.py           — token parsing + tenant resolve + admin gate
  - test_api_auth.py       — login / health / 401-403 surface

Integration (needs OpenSearch on :9200):
  - test_api_integration.py — ingest, search, dashboard, alerts, batch, retention, RBAC

Run:
  docker compose up -d opensearch
  pip install -r backend/requirements.txt
  pytest tests -q
"""
