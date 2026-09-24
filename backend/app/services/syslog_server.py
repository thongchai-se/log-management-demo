import socket
import threading

from app.config import SYSLOG_HOST, SYSLOG_PORT
from app.services.ingestion import ingest_log_document
from app.services.normalization import parse_syslog_message


def _handle_forever() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((SYSLOG_HOST, SYSLOG_PORT))
    except OSError as exc:
        print(f"[syslog] bind failed on {SYSLOG_HOST}:{SYSLOG_PORT}: {exc}")
        return

    print(f"syslog listening UDP {SYSLOG_HOST}:{SYSLOG_PORT}")

    while True:
        data, addr = sock.recvfrom(65536)
        message = data.decode("utf-8", errors="replace")
        print(f"[syslog] from {addr}: {message[:120]}")

        try:
            payload = parse_syslog_message(message, tenant="demoA")
            result = ingest_log_document(payload)
            print(f"[syslog] ingested {result.get('id')} {result.get('source')}")
        except Exception as e:
            print(f"[syslog] error: {e}")


def start_syslog_server() -> None:
    t = threading.Thread(target=_handle_forever, daemon=True)
    t.start()
