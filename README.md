# slack-drive-archiver

Slack Drive Archiver is a Python-based webhook server that listens for messages in Slack channels and automatically uploads content to Google Drive. It supports saving standalone text messages, attachments such as images or videos, and captioned posts that include both. All files are organized into folders by Slack channel and message type. This project was originally created for the purpose of archiving slack files for the University of Michigan Men's Glee Club.

## Features

The system categorizes uploaded content into Google Drive folders:

- Messages (for text-only messages)  
- Attachments (for messages with only media files like images, videos, or audio)  
- Captioned Posts (for messages that include both text and one or more attachments)  
- Miscellaneous (for any other type of file)

Each file name begins with the timestamp and ends with the sender’s username. Messages posted in Slack threads are ignored, unless they are also sent to the channel.

## Deployment

Clone the repository  
Install dependencies using pip:

```
pip install -r requirements.txt
```

Set the following environment variables:
```
export SLACK_BOT_TOKEN="xoxb-your-slack-token"
export GOOGLE_DRIVE_FOLDER_ID="root-folder-id"
export GOOGLE_CREDENTIALS_JSON='{"type": "service_account", ...}'
```
SLACK_BOT_TOKEN - your bot token from Slack 

GOOGLE_CREDENTIALS_JSON - the full JSON content from your Google service account (or create a file called credentials.json that contains the same information)

GOOGLE_DRIVE_FOLDER_ID - the ID of the parent folder in Google Drive where uploads will be organized  

To run locally:
```
python3 slack_event_server.py
```  

A web server is also needed for Slack communication. 

For local testing I used ngrok:

```
ngrok http 5000
```

For long-term deployment I used Render with a start command:

```
gunicorn slack_event_server:app --bind 0.0.0.0:$PORT
```

## Slack and Google Setup

In Slack: 
- Create an app with Event Subscriptions enabled
- Set the Request URL to the /slack/events endpoint hosted by your service (Either ngrok or Render)
- Install the app to your workspace
- Ensure the bot has OAUTH permission scopes including channels:read, channels:history, users:read, files:read, groups:history, and groups: read

In Google Cloud Console:
- Create a service account
- Download the credentials JSON
- Use the contents of the JSON to populate the GOOGLE_CREDENTIALS_JSON environment variable (or credentials.json file).
- Share your target Google Drive folder with the service account’s email address

## Notes

- Downloaded files are deleted from the server after being uploaded to Google Drive.  
- If a Slack message includes multiple attachments, all are saved and numbered.  

