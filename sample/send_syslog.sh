#!/usr/bin/env bash
# Send sample firewall syslog over UDP (default port 5514)
HOST="${1:-127.0.0.1}"
PORT="${2:-5514}"
MSG='<134>Aug 20 12:44:56 fw01 vendor=demo product=ngfw action=deny src=10.0.1.10 dst=8.8.8.8 spt=5353 dpt=53 proto=udp msg=DNS_blocked policy=Block-DNS'
printf '%s' "$MSG" | nc -u -w1 "$HOST" "$PORT"
echo "sent syslog to ${HOST}:${PORT}"
