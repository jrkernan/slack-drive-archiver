from flask import Flask, request, jsonify
import os
import json
import threading
import time
from datetime import datetime
from slack_client import download_file, get_username_from_id, get_channel_name_from_id
from drive_client import get_drive_service, upload_file_to_drive, get_or_create_subfolder

app = Flask(__name__)

# Load config from environment variables
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]

if "GOOGLE_CREDENTIALS_JSON" in os.environ:
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
else:
    with open("credentials.json") as f:
        creds_dict = json.load(f)

GOOGLE_DRIVE_FOLDER_ID = os.environ["GOOGLE_DRIVE_FOLDER_ID"]

drive_service = get_drive_service(creds_dict)
print("Drive service initialized.")

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()

    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    event = data.get("event", {})
    if event.get("type") == "message" and not event.get("thread_ts"):
        files = event.get("files", [])
        text = event.get("text", "")
        user_id = event.get("user", "unknown")
        user = get_username_from_id(user_id, SLACK_BOT_TOKEN)
        channel_id = event.get("channel", "unknown")
        channel = get_channel_name_from_id(channel_id, SLACK_BOT_TOKEN)

        timestamp = float(event['ts'])
        dt = datetime.fromtimestamp(timestamp)
        timestamp_str = dt.strftime("%Y-%m-%d_%H-%M-%S")

        def process():
            print(f"Processing message from {user} in #{channel} at {timestamp_str}")
            channel_folder = get_or_create_subfolder(drive_service, GOOGLE_DRIVE_FOLDER_ID, channel)

            has_text = text.strip() != ""
            has_attachments = any(f.get("mimetype", "").startswith(("image/", "video/")) for f in files)

            # Upload text message only
            if has_text and not has_attachments:
                msg_folder = get_or_create_subfolder(drive_service, channel_folder, "Messages")
                filename = f"message_FROM_{user}_{timestamp_str}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(text)
                upload_file_to_drive(drive_service, filename, msg_folder)
                os.remove(filename)

            # Upload each attachment
            for f_data in files:
                mimetype = f_data.get("mimetype", "")
                if mimetype.startswith(("image/", "video/")):
                    file_info = {
                        "url": f_data["url_private"],
                        "name": f_data["name"]
                    }
                    local_path = download_file(file_info, SLACK_BOT_TOKEN)
                    if local_path:
                        if has_text:
                            caption_folder = get_or_create_subfolder(drive_service, channel_folder, "Captioned Posts")
                            prefix = "caption"
                            txt_filename = f"{prefix}_FROM_{user}_{timestamp_str}.txt"
                            with open(txt_filename, "w", encoding="utf-8") as f:
                                f.write(text)
                            upload_file_to_drive(drive_service, txt_filename, caption_folder)
                            upload_name = f"{os.path.splitext(file_info['name'])[0]}_FROM_{user}_{timestamp_str}{os.path.splitext(file_info['name'])[1]}"
                            os.rename(local_path, upload_name)
                            upload_file_to_drive(drive_service, upload_name, caption_folder)
                            os.remove(txt_filename)
                            os.remove(upload_name)
                        else:
                            attach_folder = get_or_create_subfolder(drive_service, channel_folder, "Attachments")
                            upload_name = f"{os.path.splitext(file_info['name'])[0]}_FROM_{user}_{timestamp_str}{os.path.splitext(file_info['name'])[1]}"
                            os.rename(local_path, upload_name)
                            upload_file_to_drive(drive_service, upload_name, attach_folder)
                            os.remove(upload_name)

        threading.Thread(target=process).start()

    return "", 200

if __name__ == "__main__":
    app.run(port=5000)


