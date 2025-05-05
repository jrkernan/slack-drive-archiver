import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_drive_service(creds_file):
    creds = service_account.Credentials.from_service_account_file(
        creds_file,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)

def upload_file_to_drive(service, filepath, folder_id):
    file_metadata = {
        'name': os.path.basename(filepath),
        'parents': [folder_id]
    }
    media = MediaFileUpload(filepath, resumable=True)
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        supportsAllDrives=True
    ).execute()
    print(f"Uploaded to Drive: {uploaded['name']}")

def get_or_create_subfolder(service, parent_id, folder_name):
    query = (
        f"mimeType='application/vnd.google-apps.folder' and "
        f"name='{folder_name}' and '{parent_id}' in parents and trashed = false"
    )

    results = service.files().list(
        q=query,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    folders = results.get("files", [])
    if folders:
        print(f"[Drive] Reusing folder: {folder_name}")
        return folders[0]["id"]

    # If not found, create the folder
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    folder = service.files().create(
        body=metadata,
        fields="id",
        supportsAllDrives=True
    ).execute()

    print(f"[Drive] Created new folder: {folder_name}")
    return folder["id"]

