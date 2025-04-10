import os
import requests
import json
import threading
import pandas as pd
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define bot configurations in a DataFrame
bot_configs = pd.DataFrame([
    {
        "name": "DummyBot",
        "bot_token": os.environ.get("DUMMY_BOT_TOKEN"),
        "app_token": os.environ.get("DUMMY_APP_TOKEN"),
        "ping_url": "http://35.236.125.235:8501/api/v1/run/70769140-1841-468d-81fe-eac021cf7ac8?stream=false"
    },
    {
        "name": "DummyBot2",
        "bot_token": os.environ.get("DUMMY_BOT2_TOKEN"),
        "app_token": os.environ.get("DUMMY_APP2_TOKEN"),
        "ping_url": "http://127.0.0.1:7860/api/v1/run/595fb00d-675f-49e4-8283-ff9ec4fc40d7?stream=false"
    }
])

def start_bot(bot_name, bot_token, app_token, ping_url):
    if not bot_token or not app_token:
        print(f"Error: Tokens are required for {bot_name}")
        return

    app = App(token=bot_token)

    # @app.event("message")  # Listen to message events
    # def handle_message_events(body, logger, say):
    #     # logger.info(f"Message event received for {bot_name}")
    #     # event = body.get("event", {})
    #     # message_text = event.get("text", "")
    #     # data = {
    #     #     "input_value": message_text,
    #     #     "input_type": "text",
    #     #     "output_type": "text"
    #     # }
    #     # forward_event(data, ping_url)
    #     say("hi")

    # @app.middleware
    # def log_everything(context, payload, next):
    #     print("=" * 40)
    #     print(f"📦 Incoming payload:")
    #     print(json.dumps(payload, indent=2))
    #     print("=" * 40)
    #     return next()
    
    @app.middleware
    def handle_all_events(body, logger, next):
        logger.info(f"event received for {bot_name}")
        print(bot_name, " is receiving an event")
        event = body.get("event", {})
        event_str = json.dumps(event)  # Convert event to a JSON string
        print("event_str: ", event_str)
        data = {
            "input_value": event_str,
            "input_type": "text",
            "output_type": "text"
        }
        forward_event(data, ping_url)

        next()
    # app.middleware(handle_all_events)

    # @app.event("app_mention")  # Listen to app mention events
    # def handle_app_mention_events(body, logger):
    #     # logger.info(f"App mention event received for {bot_name}")
    #     # event = body.get("event", {})
    #     # event_str = json.dumps(event)  # Convert event to a JSON string
    #     # print("event_str: ", event_str)
    #     # data = {
    #     #     "input_value": event_str,
    #     #     "input_type": "text",
    #     #     "output_type": "text"
    #     # }
    #     # forward_event(data, ping_url)
    #     print("event received for app mention")

#     @app.event("reaction_added")  # Listen to reaction added events
#     def handle_reaction_added_events(body, logger):
#         # logger.info(f"Reaction added event received for {bot_name}")
#         # event = body.get("event", {})
#         # event_str = json.dumps(event)  # Convert event to a JSON string
#         # data = {
#         #     "input_value": event_str,
#         #     "input_type": "text",
#         #     "output_type": "text"
#         # }
#         # forward_event(data, ping_url)
#         print("event received for reaction added")

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
    for _, row in bot_configs.iterrows():
        thread = threading.Thread(target=start_bot, args=(row['name'], row['bot_token'], row['app_token'], row['ping_url']))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()