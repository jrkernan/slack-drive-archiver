from flask import Flask, request, jsonify
import os
import json
import threading
from datetime import datetime
from slack_client import (
    download_file,
    get_username_from_id,
    get_channel_name_from_id,
)
from drive_client import (
    get_drive_service,
    upload_file_to_drive,
    get_or_create_subfolder,
)

app = Flask(__name__)

# Load config from environment variables
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
GOOGLE_CREDENTIALS_JSON = os.environ["GOOGLE_CREDENTIALS_JSON"]
GOOGLE_DRIVE_FOLDER_ID = os.environ["GOOGLE_DRIVE_FOLDER_ID"]

creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
drive_service = get_drive_service(creds_dict)
print("Drive service initialized.")

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()

    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    event = data.get("event", {})
    if event.get("type") == "message" and "subtype" not in event:
        is_text_only = not event.get("files") and event.get("text", "").strip() != ""
        is_thread_reply = event.get("thread_ts") and event["thread_ts"] != event["ts"]

        # Skip if it's just a text reply in a thread
        if is_text_only and is_thread_reply:
            return "", 200

        files = event.get("files", [])
        text = event.get("text", "")
        user_id = event.get("user", "unknown")
        user = get_username_from_id(user_id, SLACK_BOT_TOKEN)
        channel_id = event.get("channel", "unknown")
        channel = get_channel_name_from_id(channel_id, SLACK_BOT_TOKEN)

        timestamp = float(event["ts"])
        dt = datetime.fromtimestamp(timestamp)
        timestamp_str = dt.strftime("%Y-%m-%d_%H-%M-%S")

        def process():
            print(f"Processing message from {user} in #{channel} at {timestamp_str}")
            channel_folder = get_or_create_subfolder(
                drive_service, GOOGLE_DRIVE_FOLDER_ID, channel
            )

            has_text = text.strip() != ""
            has_attachments = bool(files)

            # Upload text-only message
            if has_text and not has_attachments:
                msg_folder = get_or_create_subfolder(
                    drive_service, channel_folder, "Messages"
                )
                filename = f"{timestamp_str}_FROM_{user}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(text)
                upload_file_to_drive(drive_service, filename, msg_folder)
                os.remove(filename)

            caption_uploaded = False
            attachment_counter = 1
            total_attachments = len(files)

            for f_data in files:
                mimetype = f_data.get("mimetype", "")
                file_info = {
                    "url": f_data["url_private"],
                    "name": f_data["name"]
                }
                local_path = download_file(file_info, SLACK_BOT_TOKEN)
                if not local_path:
                    continue

                # Determine category
                if mimetype.startswith(("image/", "video/")):
                    category = "Captioned Posts" if has_text else "Attachments"
                else:
                    category = "Miscellaneous"

                folder = get_or_create_subfolder(drive_service, channel_folder, category)

                # Upload caption once
                if has_text and category == "Captioned Posts" and not caption_uploaded:
                    caption_filename = f"{timestamp_str}_FROM_{user}.txt"
                    with open(caption_filename, "w", encoding="utf-8") as f:
                        f.write(text)
                    upload_file_to_drive(drive_service, caption_filename, folder)
                    os.remove(caption_filename)
                    caption_uploaded = True

                ext = os.path.splitext(file_info["name"])[1]
                if total_attachments == 1:
                    base = f"{timestamp_str}_FROM_{user}"
                else:
                    base = f"{timestamp_str}_{attachment_counter}_FROM_{user}"
                upload_name = f"{base}{ext}"

                os.rename(local_path, upload_name)
                upload_file_to_drive(drive_service, upload_name, folder)
                os.remove(upload_name)

                attachment_counter += 1

        threading.Thread(target=process).start()

    return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    