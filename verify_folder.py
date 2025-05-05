from google.oauth2 import service_account
from googleapiclient.discovery import build

FOLDER_ID = "1FPOvPz3G16140iB1UE67dlyV_T9oT9PK"
CREDS_FILE = "credentials.json"

creds = service_account.Credentials.from_service_account_file(
    CREDS_FILE,
    scopes=["https://www.googleapis.com/auth/drive"]
)

service = build("drive", "v3", credentials=creds)

# Check the file type of the ID
metadata = service.files().get(
    fileId=FOLDER_ID,
    fields="id, name, mimeType",
    supportsAllDrives=True
).execute()


print("Folder metadata:")
print(metadata)
