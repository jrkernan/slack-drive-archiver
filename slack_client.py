import os
import requests
from slack_sdk import WebClient

def get_username_from_id(user_id, token):
    client = WebClient(token=token)
    try:
        response = client.users_info(user=user_id)
        if response["ok"]:
            user = response["user"]
            return user.get("real_name") or user.get("name") or user_id
    except Exception as e:
        print(f"Could not fetch username: {e}")
    return user_id  # fallback to ID if it fails


def download_file(file_info, token, output_folder="downloads"):
    os.makedirs(output_folder, exist_ok=True)
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(file_info['url'], headers=headers)

    if response.status_code == 200:
        filepath = os.path.join(output_folder, file_info['name'])
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
    else:
        print(f"Failed to download {file_info['name']} (status: {response.status_code})")
    return None

def get_channel_name_from_id(channel_id, token):
    url = "https://slack.com/api/conversations.info"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"channel": channel_id}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    if not data.get("ok"):
        print(f"[ERROR] Failed to fetch channel name: {data}")
        return "unknown-channel"

    return data["channel"]["name"]
