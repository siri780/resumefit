import time
from datetime import datetime

from app.applications import TIMEZONE
from app.notify import format_alert, send_telegram
from app.scan import scan

INTERVAL_SECONDS = 5 * 60
WORKDAY_EVERY = 6
MAX_ALERTS = 10


def run_once(cycle):
    """One scan: send the best new matches to your phone."""
    include_workday = cycle % WORKDAY_EVERY == 0
    matches, errors, total = scan(include_workday)
    for match in matches[:MAX_ALERTS]:
        send_telegram(format_alert(match))
    if len(matches) > MAX_ALERTS:
        send_telegram(f"…and {len(matches) - MAX_ALERTS} more new matches.")
    now = datetime.now(TIMEZONE).strftime("%H:%M")
    print(f"[{now}] checked {total} jobs · {len(matches)} matches · "
          f"{len(errors)} errors · workday={include_workday}", flush=True)


if __name__ == "__main__":
    send_telegram("👀 ResumeFit watcher started. Checking every 5 minutes.")
    cycle = 0
    while True:
        try:
            run_once(cycle)
        except Exception as error:
            print(f"Scan failed: {error}", flush=True)
        cycle += 1
        time.sleep(INTERVAL_SECONDS)