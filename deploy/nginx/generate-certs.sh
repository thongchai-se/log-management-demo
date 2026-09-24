#!/usr/bin/env bash
# Generate self-signed TLS cert for SaaS / local HTTPS demo
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$DIR/certs"
mkdir -p "$OUT"

openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout "$OUT/server.key" \
  -out "$OUT/server.crt" \
  -days 365 \
  -subj "/CN=localhost/O=LogManagementDemo/C=TH"

echo "Wrote $OUT/server.crt and $OUT/server.key"
echo "Browser will warn on self-signed cert — click Advanced → Proceed."
