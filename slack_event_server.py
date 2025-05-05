from flask import Flask, request, jsonify
import os
import json
import threading
from datetime import datetime

from slack_client import (
    download_file,
    get_username_from_id,
    get_channel_name_from_id
)
from drive_client import (
    get_drive_service,
    upload_file_to_drive,
    get_or_create_subfolder
)

app = Flask(__name__)

# Load config
with open("config.json") as f:
    config = json.load(f)

SLACK_BOT_TOKEN = config["slack_bot_token"]
GOOGLE_CREDENTIALS_FILE = config["google_credentials_file"]
ARCHIVE_FOLDER_ID = config["slack_archive_folder_id"]

drive_service = get_drive_service(GOOGLE_CREDENTIALS_FILE)
print("Using credentials file:", GOOGLE_CREDENTIALS_FILE)

# Folder cache to prevent duplicate creation
subfolder_cache = {}

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()

    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    event = data.get("event", {})

    # Ignore thread replies
    if event.get("thread_ts") and event["thread_ts"] != event["ts"]:
        print("Skipping thread reply")
        return "", 200

    if event.get("type") == "message":
        files = event.get("files", [])
        text = event.get("text", "")
        user_id = event.get("user", "unknown")
        user = get_username_from_id(user_id, SLACK_BOT_TOKEN)
        channel_id = event.get("channel")
        channel_name = get_channel_name_from_id(channel_id, SLACK_BOT_TOKEN).strip()


        def process():
            ts = float(event["ts"])
            dt = datetime.fromtimestamp(ts)
            timestamp_str = dt.strftime("%Y-%m-%d_%H-%M-%S")

            has_text = bool(text.strip())
            has_files = any(f.get("mimetype", "").startswith(("image/", "video/")) for f in files)

            # Decide target category folder
            if has_text and has_files:
                category = "Captioned Posts"
            elif has_text:
                category = "Messages"
            elif has_files:
                category = "Attachments"
            else:
                return  # Skip completely empty messages

            # Step 1: Get or create the channel folder
            channel_folder_id = subfolder_cache.get(channel_name)
            if not channel_folder_id:
                channel_folder_id = get_or_create_subfolder(drive_service, ARCHIVE_FOLDER_ID, channel_name)
                subfolder_cache[channel_name] = channel_folder_id

            # Step 2: Get or create the category folder inside the channel
            subfolder_key = f"{channel_name}/{category}"
            category_folder_id = subfolder_cache.get(subfolder_key)
            if not category_folder_id:
                category_folder_id = get_or_create_subfolder(drive_service, channel_folder_id, category)
                subfolder_cache[subfolder_key] = category_folder_id

            # Upload message text
            if has_text:
                os.makedirs("messages", exist_ok=True)
                prefix = "caption" if category == "Captioned Posts" else category.lower()
                txt_filename = f"{prefix}_FROM_{user}_{timestamp_str}.txt"
                filepath = os.path.join("messages", txt_filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(text)
                upload_file_to_drive(drive_service, filepath, category_folder_id)

            # Upload image/video files
            for f_data in files:
                mimetype = f_data.get("mimetype", "")
                if mimetype.startswith(("image/", "video/")):
                    file_info = {
                        "url": f_data["url_private"],
                        "name": f_data["name"]
                    }
                    local_path = download_file(file_info, SLACK_BOT_TOKEN)
                    if local_path:
                        orig_name = file_info["name"]
                        name_root, ext = os.path.splitext(orig_name)
                        new_name = f"{name_root}_FROM_{user}_{timestamp_str}{ext}"

                        os.makedirs("attachments", exist_ok=True)
                        new_path = os.path.join("attachments", new_name)
                        os.rename(local_path, new_path)
                        upload_file_to_drive(drive_service, new_path, category_folder_id)

        threading.Thread(target=process).start()

    return "", 200

if __name__ == "__main__":
    app.run(port=5000)



