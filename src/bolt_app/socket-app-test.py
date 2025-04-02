import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Load from environment variables
SLACK_BOT_TOKEN = os.getenv("DUMMY_BOT3_TOKEN")
print(SLACK_BOT_TOKEN)
SLACK_APP_TOKEN = os.getenv("DUMMY_APP3_TOKEN")
app = App(token=SLACK_BOT_TOKEN)
# Catch ALL events (even ones without a handler)
@app.use
def log_everything(context, payload, next):
    print("=" * 40)
    print(f"📦 Incoming payload:")
    print(json.dumps(payload, indent=2))
    print("=" * 40)
    return next()

@app.event("app_mention")
def handle_app_mention_events(body, logger):
    logging.info(body)
    print(body)

if __name__ == "__main__":
    print("Starting Slack event logger...")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()