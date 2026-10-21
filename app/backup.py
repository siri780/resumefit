import os
import subprocess

from app.applications import APPS_DIR

REPO = "siri780/resumefit-applications"


def git(*args):
    """Run a git command inside the applications folder."""
    return subprocess.run(["git", "-C", str(APPS_DIR), *args],
                          capture_output=True, text=True)


def repo_url(token):
    return f"https://x-access-token:{token}@github.com/{REPO}.git"


def restore():
    """If the applications folder is missing, bring it back from the private repo."""
    token = os.getenv("APPS_REPO_TOKEN")
    if not token or (APPS_DIR / ".git").exists():
        return
    subprocess.run(["git", "clone", "-q", repo_url(token), str(APPS_DIR)],
                   capture_output=True, text=True)
    git("remote", "set-url", "origin", f"https://github.com/{REPO}.git")


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

    push = git("push", repo_url(token), "main")
    if push.returncode != 0:
        error = push.stderr.replace(token, "***").strip()
        return False, f"Backup failed: {error[-300:]}"
    return True, "✅ Backed up to private GitHub repo"