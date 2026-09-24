import threading
import time

from app.services.index_setup import purge_old_logs

# Run purge once per hour
INTERVAL_SECONDS = 3600


def _loop() -> None:
    # First run shortly after boot so demos see retention working
    time.sleep(15)
    while True:
        try:
            purge_old_logs()
        except Exception as exc:
            print(f"[retention] error: {exc}")
        time.sleep(INTERVAL_SECONDS)


def start_retention_worker() -> None:
    t = threading.Thread(target=_loop, daemon=True, name="retention-worker")
    t.start()
    print("[retention] worker started")
