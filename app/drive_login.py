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
    flow = Flow.from_client_config(client_config(), scopes=SCOPES,
                                   redirect_uri=REDIRECT)
    url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    print("\n1) Open this link and allow access:\n")
    print(url)
    print("\n2) Your browser will then show an error page. That is expected.")
    print("   Copy the FULL address from the address bar and paste it below.\n")
    pasted = input("Paste address here: ").strip()
    code = parse_qs(urlparse(pasted).query)["code"][0]
    flow.fetch_token(code=code)
    print("\n3) Save this as a Codespaces secret named GOOGLE_REFRESH_TOKEN:\n")
    print(flow.credentials.refresh_token)