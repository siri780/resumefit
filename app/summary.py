"""A short evening summary in Telegram: what ResumeFit did today."""
import html
from datetime import datetime

from app.applications import TIMEZONE

SUMMARY_HOUR = 20          # 8 PM New York time
DAILY_GOAL = 23            # ~700 applications a month


def setup(con):
    con.execute("CREATE TABLE IF NOT EXISTS daily "
                "(day TEXT, name TEXT, value INTEGER, PRIMARY KEY (day, name))")
    con.execute("CREATE TABLE IF NOT EXISTS day_alerts "
                "(day TEXT, score INTEGER, company TEXT, title TEXT, url TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS state "
                "(name TEXT PRIMARY KEY, value TEXT)")


def today():
    return datetime.now(TIMEZONE).date().isoformat()


def bump(con, name, amount=1):
    """Add to one of today's counters (alerts, tailored, ...)."""
    if not amount:
        return
    setup(con)
    con.execute("INSERT INTO daily VALUES (?, ?, ?) ON CONFLICT(day, name) "
                "DO UPDATE SET value = value + excluded.value",
                (today(), name, amount))
    con.commit()


def record_alert(con, match):
    """Remember an alert so the summary can list the day's best jobs."""
    setup(con)
    con.execute("INSERT INTO day_alerts VALUES (?, ?, ?, ?, ?)",
                (today(), match.get("score") or 0, match["company"],
                 match["title"], match["url"]))
    con.commit()
    bump(con, "alerts")


def summary_text(con, day=None):
    setup(con)
    day = day or today()
    counts = dict(con.execute("SELECT name, value FROM daily WHERE day = ?",
                              (day,)).fetchall())
    best = con.execute("SELECT company, title, url FROM day_alerts WHERE day = ? "
                       "ORDER BY score DESC LIMIT 5", (day,)).fetchall()
    e = html.escape
    lines = ["📊 <b>ResumeFit · today</b>",
             f"🆕 Job alerts sent: {counts.get('alerts', 0)}",
             f"✨ Resumes tailored: {counts.get('tailored', 0)}",
             f"📬 Applications logged: {counts.get('applied', 0)} / {DAILY_GOAL} "
             "daily goal (≈700 a month)",
             f"❌ Rejections: {counts.get('rejected', 0)}"]
    if best:
        lines.append("\n<b>Today's best matches</b> (apply if you haven't):")
        for company, title, url in best:
            lines.append(f"• <a href=\"{e(url)}\">{e(company)} · {e(title)}</a>")
    else:
        lines.append("\nNo new matching jobs today.")
    return "\n".join(lines)


def maybe_send_summary(con, send):
    """Send the summary once a day, after SUMMARY_HOUR. Returns True if sent."""
    setup(con)
    now = datetime.now(TIMEZONE)
    if now.hour < SUMMARY_HOUR:
        return False
    row = con.execute("SELECT value FROM state WHERE name = 'summary_day'"
                      ).fetchone()
    if row and row[0] == today():
        return False
    send(summary_text(con))
    con.execute("INSERT OR REPLACE INTO state VALUES ('summary_day', ?)",
                (today(),))
    con.commit()
    return True
