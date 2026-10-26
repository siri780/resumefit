import os
from urllib.parse import parse_qs, urlparse

from google_auth_oauthlib.flow import Flow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
REDIRECT = "http://localhost:8080/"


def client_config():
    """Build Google's login settings from your Codespaces secrets."""
    return {"installed": {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [REDIRECT],
    }}


if __name__ == "__main__":
    import sys
    gmail = "--gmail" in sys.argv
    if gmail:
        from app.mail_alerts import GMAIL_SCOPES as scopes
        secret_name = "GMAIL_REFRESH_TOKEN"
    else:
        scopes, secret_name = SCOPES, "GOOGLE_REFRESH_TOKEN"
    flow = Flow.from_client_config(client_config(), scopes=scopes,
                                   redirect_uri=REDIRECT)
    url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    print("\n1) Open this link and allow access:\n")
    print(url)
    print("\n2) Your browser will then show an error page. That is expected.")
    print("   Copy the FULL address from the address bar and paste it below.\n")
    pasted = input("Paste address here: ").strip()
    code = parse_qs(urlparse(pasted).query)["code"][0]
    flow.fetch_token(code=code)
    where = "GitHub Actions secret" if gmail else "Codespaces secret"
    print(f"\n3) Save this as a {where} named {secret_name}:\n")
    print(flow.credentials.refresh_token)