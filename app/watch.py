import sys
import time
from datetime import datetime, timedelta

from app.applications import TIMEZONE
from app.notify import format_alert, send_telegram
from app.scan import connect, scan, scan_email
from app.summary import bump, maybe_send_summary, record_alert
from app.app_emails import sync_applications, sync_message
from app.taps import process_taps, remember_alert, send_message

INTERVAL_SECONDS = 60
SCAN_EVERY = timedelta(minutes=4, seconds=30)
WORKDAY_EVERY = timedelta(minutes=29)
MAX_ALERTS = 10


def due(con, name, every):
    """True (and remember now) if `every` has passed since `name` last ran."""
    con.execute("CREATE TABLE IF NOT EXISTS state "
                "(name TEXT PRIMARY KEY, value TEXT)")
    row = con.execute("SELECT value FROM state WHERE name = ?",
                      (name,)).fetchone()
    now = datetime.now(TIMEZONE)
    if row and now - datetime.fromisoformat(row[0]) < every:
        return False
    con.execute("INSERT OR REPLACE INTO state VALUES (?, ?)",
                (name, now.isoformat()))
    con.commit()
    return True


def run_once():
    """Handle button taps every run; scan for new jobs every ~5 minutes."""
    con = connect()
    try:
        tapped = process_taps(con)
    except Exception as error:
        tapped = 0
        print(f"Tap handling failed: {error}", flush=True)
    bump(con, "tailored", tapped)
    try:
        maybe_send_summary(con, send_message)
    except Exception as error:
        print(f"Summary failed: {error}", flush=True)
    now = datetime.now(TIMEZONE).strftime("%H:%M")
    if not due(con, "scan", SCAN_EVERY):
        print(f"[{now}] taps only · tailored={tapped}", flush=True)
        return
    include_workday = due(con, "workday", WORKDAY_EVERY)
    matches, errors, total = scan(include_workday)
    mail_matches, mail_errors = scan_email(con)
    errors += mail_errors
    matches = mail_matches + matches
    for match in matches[:MAX_ALERTS]:
        # The Tailor button needs the job description to work with.
        buttons = (remember_alert(con, match) if match.get("description")
                   else None)
        send_message(format_alert(match), buttons)
        record_alert(con, match)
    try:
        synced = sync_applications(con)
    except Exception as error:
        synced = None
        errors.append(f"Application emails: {type(error).__name__}")
    if synced and (synced[0] or synced[1]):
        added, rejected, added_today = synced
        send_message(sync_message(added, rejected))
        bump(con, "applied", added_today)
        bump(con, "rejected", len(rejected))
    if len(matches) > MAX_ALERTS:
        send_telegram(f"…and {len(matches) - MAX_ALERTS} more new matches.")
    print(f"[{now}] checked {total} jobs · {len(matches)} matches · "
          f"{len(errors)} errors · workday={include_workday} · "
          f"tailored={tapped} · from email={len(mail_matches)}", flush=True)
    if errors:
        print("Errors: " + "; ".join(errors), flush=True)


if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        send_telegram("👀 ResumeFit watcher started. Checking every minute.")
        while True:
            try:
                run_once()
            except Exception as error:
                print(f"Run failed: {error}", flush=True)
            time.sleep(INTERVAL_SECONDS)
