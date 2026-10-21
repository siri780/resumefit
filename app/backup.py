import os
import subprocess

from app.applications import APPS_DIR

REPO = "siri780/resumefit-applications"


def git(*args):
    """Run a git command inside the applications folder."""
    return subprocess.run(["git", "-C", str(APPS_DIR), *args],
                          capture_output=True, text=True)


def backup(message):
    """Commit and push the applications folder to the private repo.

    Returns (ok, text) so the web app can show what happened.
    """
    token = os.getenv("APPS_REPO_TOKEN")
    if not token:
        return False, "Backup skipped: APPS_REPO_TOKEN is not set"

    if not (APPS_DIR / ".git").exists():
        git("init", "-b", "main")
        git("config", "user.name", "Shirisha Gajendra")
        git("config", "user.email", "gshirisha235@gmail.com")

    git("add", "-A")
    git("commit", "-m", message)

    url = f"https://x-access-token:{token}@github.com/{REPO}.git"
    push = git("push", url, "main")
    if push.returncode != 0:
        error = push.stderr.replace(token, "***").strip()
        return False, f"Backup failed: {error[-300:]}"
    return True, "✅ Backed up to private GitHub repo"