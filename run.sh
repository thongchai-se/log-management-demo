#!/usr/bin/env bash
# One-command appliance bring-up
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f deploy/nginx/certs/server.crt ]; then
  bash deploy/nginx/generate-certs.sh
fi

docker compose up -d --build
echo ""
echo "Appliance is starting..."
echo "  UI (HTTPS):  https://localhost"
echo "  API docs:    https://localhost/docs"
echo "  Health:      https://localhost/health"
echo "  Syslog UDP:  localhost:5514"
echo ""
echo "Demo users: admin/admin123  |  viewer/viewer123"
echo "Seed samples:  make seed   (or python sample/post_logs.py)"
