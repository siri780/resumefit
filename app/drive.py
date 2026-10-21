import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.drive_login import SCOPES

ROOT_FOLDER = "ResumeFit Applications"
FOLDER_TYPE = "application/vnd.google-apps.folder"


def drive_service():
    """Connect to Google Drive using your saved secrets."""
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def find_or_create_folder(service, name, parent=None):
    """Return the id of a Drive folder, creating it if needed."""
    query = f"name = '{name}' and mimeType = '{FOLDER_TYPE}' and trashed = false"
    if parent:
        query += f" and '{parent}' in parents"
    found = service.files().list(q=query, fields="files(id)").execute()["files"]
    if found:
        return found[0]["id"]
    body = {"name": name, "mimeType": FOLDER_TYPE}
    if parent:
        body["parents"] = [parent]
    return service.files().create(body=body, fields="id").execute()["id"]


def upload_file(service, path, parent):
    """Upload a file into a Drive folder, replacing an older copy."""
    query = f"name = '{path.name}' and '{parent}' in parents and trashed = false"
    found = service.files().list(q=query, fields="files(id)").execute()["files"]
    media = MediaFileUpload(str(path))
    if found:
        service.files().update(fileId=found[0]["id"], media_body=media).execute()
    else:
        service.files().create(body={"name": path.name, "parents": [parent]},
                               media_body=media, fields="id").execute()


def upload_to_drive(tracker, folder=None):
    """Upload the tracker (and one application folder). Returns (ok, text)."""
    if not os.getenv("GOOGLE_REFRESH_TOKEN"):
        return False, "Drive upload skipped: Google Drive is not connected"
    try:
        service = drive_service()
        root = find_or_create_folder(service, ROOT_FOLDER)
        if folder:
            app_folder = find_or_create_folder(service, folder.name, root)
            for path in sorted(folder.iterdir()):
                if path.is_file():
                    upload_file(service, path, app_folder)
        if tracker.exists():
            upload_file(service, tracker, root)
        return True, "✅ Uploaded to Google Drive"
    except Exception as error:
        return False, f"Drive upload failed: {error}"