import sys
import time
from datetime import datetime

from app.applications import TIMEZONE
from app.notify import format_alert, send_telegram
from app.scan import connect, scan
from app.taps import process_taps, remember_alert, send_message

INTERVAL_SECONDS = 5 * 60
WORKDAY_EVERY = 6
MAX_ALERTS = 10


def run_once(cycle):
    """Handle button taps, then send the best new matches to your phone."""
    con = connect()
    try:
        tapped = process_taps(con)
    except Exception as error:
        tapped = 0
        print(f"Tap handling failed: {error}", flush=True)
    include_workday = cycle % WORKDAY_EVERY == 0
    matches, errors, total = scan(include_workday)
    for match in matches[:MAX_ALERTS]:
        send_message(format_alert(match), remember_alert(con, match))
    if len(matches) > MAX_ALERTS:
        send_telegram(f"…and {len(matches) - MAX_ALERTS} more new matches.")
    now = datetime.now(TIMEZONE).strftime("%H:%M")
    print(f"[{now}] checked {total} jobs · {len(matches)} matches · "
          f"{len(errors)} errors · workday={include_workday} · "
          f"tailored={tapped}", flush=True)


if __name__ == "__main__":
    if "--once" in sys.argv:
        minute = datetime.now(TIMEZONE).minute
        run_once(0 if minute % 30 < 6 else 1)
    else:
        send_telegram("👀 ResumeFit watcher started. Checking every 5 minutes.")
        cycle = 0
        while True:
            try:
                run_once(cycle)
            except Exception as error:
                print(f"Scan failed: {error}", flush=True)
            cycle += 1
            time.sleep(INTERVAL_SECONDS)