import os
import requests
import json
import threading
import pandas as pd
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from flask import Flask

# Create Flask app
flask_app = Flask(__name__)

@flask_app.route("/")
def health_check():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    flask_app.run(host="0.0.0.0", port=port)

# Load environment variables
load_dotenv()

# Define bot configurations in a DataFrame
bot_configs = pd.DataFrame([
    {
        "name": "DummyBot",
        "bot_token": os.environ.get("DUMMY_BOT_TOKEN"),
        "app_token": os.environ.get("DUMMY_APP_TOKEN"),
        "ping_url": "http://0.0.0.0:8502/api/v1/run/ac6b8811-6741-435d-97a8-3674bd683397?stream=false"
    },
    {
        "name": "DummyBot2",
        "bot_token": os.environ.get("DUMMY_BOT2_TOKEN"),
        "app_token": os.environ.get("DUMMY_APP2_TOKEN"),
        "ping_url": "http://35.236.125.235:8501/api/v1/run/70769140-1841-468d-81fe-eac021cf7ac8?stream=false"
    }
])

def start_bot(bot_name, bot_token, app_token, ping_url):
    if not bot_token or not app_token:
        print(f"Error: Tokens are required for {bot_name}")
        return

    app = App(token=bot_token)

    # @app.event("message")  # Listen to message events
    # def handle_message_events(body, logger):
    #     logger.info(f"Message event received for {bot_name}")
    #     event = body.get("event", {})
    #     message_text = event.get("text", "")
    #     data = {
    #         "input_value": message_text,
    #         "input_type": "text",
    #         "output_type": "text"
    #     }
    #     forward_event(data, ping_url)

    @app.event("app_mention")  # Listen to app mention events
    def handle_app_mention_events(body, logger):
        logger.info(f"App mention event received for {bot_name}")
        event = body.get("event", {})
        event_str = json.dumps(event)  # Convert event to a JSON string
        print("event_str: ", event_str)
        data = {
            "input_value": event_str,
            "input_type": "text",
            "output_type": "text"
        }
        forward_event(data, ping_url)

    @app.event("reaction_added")  # Listen to reaction added events
    def handle_reaction_added_events(body, logger):
        logger.info(f"Reaction added event received for {bot_name}")
        event = body.get("event", {})
        event_str = json.dumps(event)  # Convert event to a JSON string
        data = {
            "input_value": event_str,
            "input_type": "text",
            "output_type": "text"
        }
        forward_event(data, ping_url)

    print(f"Info: Starting {bot_name} in Socket Mode!")
    handler = SocketModeHandler(app, app_token)
    handler.start()

# Helper function to forward events
def forward_event(data, ping_url):
    print("forwarding the event to the agent: ", data)
    try:
        response = requests.post(
            ping_url,
            headers={"Content-Type": "application/json"},
            json=data,
            timeout=5
        )
        if response.status_code >= 200 and response.status_code < 300:
            print("Info: Successfully pinged URL")
        else:
            print(f"Error: Failed to ping URL. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error: Exception while pinging URL: {str(e)}")

if __name__ == "__main__":
    threads = []
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    threads.append(flask_thread)
    

    for _, row in bot_configs.iterrows():
        thread = threading.Thread(target=start_bot, args=(row['name'], row['bot_token'], row['app_token'], row['ping_url']))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()