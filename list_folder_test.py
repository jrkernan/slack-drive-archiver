from google.oauth2 import service_account
from googleapiclient.discovery import build

FOLDER_ID = "1FPOvPz3G16140iB1UE67dlyV_T9oT9PK"
CREDS_FILE = "credentials.json"

creds = service_account.Credentials.from_service_account_file(
    CREDS_FILE,
    scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=creds)

# Try listing contents in the folder
query = f"'{FOLDER_ID}' in parents"
results = service.files().list(q=query, fields="files(id, name)").execute()
files = results.get("files", [])

print("Files accessible in folder:")
for f in files:
    print(f"{f['name']} ({f['id']})")
