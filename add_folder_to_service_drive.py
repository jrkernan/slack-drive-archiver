from google.oauth2 import service_account
from googleapiclient.discovery import build

FOLDER_ID = "1FPOvPz3G16140iB1UE67dlyV_T9oT9PK"
CREDS_FILE = "credentials.json"

creds = service_account.Credentials.from_service_account_file(
    CREDS_FILE,
    scopes=["https://www.googleapis.com/auth/drive"]
)

service = build("drive", "v3", credentials=creds)

# Try to create a shortcut to the shared folder
shortcut_metadata = {
    'name': 'SharedFolderShortcut',
    'mimeType': 'application/vnd.google-apps.shortcut',
    'shortcutDetails': {
        'targetId': FOLDER_ID
    }
}

try:
    shortcut = service.files().create(body=shortcut_metadata, fields="id").execute()
    print("Shortcut created:", shortcut["id"])
except Exception as e:
    print("Failed to create shortcut:", e)
