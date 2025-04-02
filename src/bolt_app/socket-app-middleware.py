import os
import requests
import json
import threading
import pandas as pd
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.error import BoltUnhandledRequestError
from dotenv import load_dotenv
import logging
import traceback

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define bot configurations in a DataFrame
bot_configs = pd.DataFrame([
    # {
    #     "name": "DummyBot2",
    #     "bot_token": os.environ.get("DUMMY_BOT2_TOKEN"),
    #     "app_token": os.environ.get("DUMMY_APP2_TOKEN"),
    #     "ping_url": "http://35.236.125.235:8501/api/v1/run/70769140-1841-468d-81fe-eac021cf7ac8?stream=false"
    # },
    {
        "name": "DummyBot",
        "bot_token": os.environ.get("DUMMY_BOT_TOKEN"),
        "app_token": os.environ.get("DUMMY_APP_TOKEN"),
        "ping_url": "http://0.0.0.0:8501/api/v1/run/a7f4a5aa-8fdd-4cb3-ba67-4682d630bb9c?stream=false"
    }
])

# Assume the API Key environment variable name
FLOW_API_KEY = os.environ.get("FLOW_API_KEY")

def start_bot(bot_name, bot_token, app_token, ping_url, api_key):
    if not bot_token or not app_token:
        logging.error(f"Tokens are required for {bot_name}, bot cannot start.")
        return

    app = App(token=bot_token, raise_error_for_unhandled_request=False)
    @app.middleware
    def log_everything(context, payload, next):
        print("=" * 40)
        print(f"📦 Incoming payload:")
        print(json.dumps(payload, indent=2))
        print("=" * 40)
        return next()
    @app.middleware
    def handle_all_events(body, logger, next, context):
        logger.info(f"event received for {bot_name}")
        event = body.get("event", {})
        event_str = json.dumps(event)  # Convert event to a JSON string
        logger.info(f"Event String for {bot_name}: {event_str}")
        data = {
            "input_value": event_str,
            "input_type": "text",
            "output_type": "text"
        }
        try:
            forward_event(data, ping_url, api_key, bot_name)
        except Exception as e:
            logging.error(f"Error forwarding event for {bot_name}: {e}")
            logging.error(traceback.format_exc())
        # next()
        context.ack()

  
    # @app.error
    # def handle_errors(error, body, logger):
    #     """Global error handler to catch and log errors, especially unhandled requests."""
    #     logger.error(f"({bot_name}) Uncaught error: {error}")
    #     # Log the body of the request that caused the error
    #     logger.error(f"({bot_name}) Request body: {body}")
    #     # For BoltUnhandledRequestError, Bolt itself usually returns a 404.
    #     # For other errors, you might want to return a specific response,
    #     # but for debugging, just logging is often sufficient.

    # print(f"Info: Starting {bot_name} in Socket Mode!")

    try:
        handler = SocketModeHandler(app, app_token)
        handler.start()
    except Exception as e:
        logging.error(f"Error starting Socket Mode handler for {bot_name}: {e}")
        logging.error(traceback.format_exc())

# Helper function to forward events
def forward_event(data, ping_url, api_key, bot_name):
    print("forwarding the event to ", bot_name, ": ", data)
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers['x-api-key'] = api_key
        print("Info: Adding x-api-key header")
    else:
        logging.warning("FLOW_API_KEY not set. Proceeding without x-api-key header.")

    try:
        response = requests.post(
            ping_url,
            headers=headers,
            json=data,
            timeout=10
        )
        print("response: ", response)
        if response.status_code >= 200 and response.status_code < 300:
            logging.info("Info: Successfully pinged URL")
        else:
            logging.error(f"Failed to ping URL. Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        logging.error(f"Exception while pinging URL: {str(e)}")

if __name__ == "__main__":
    # Retrieve the shared API key from environment variable
    flow_api_key = os.environ.get("FLOW_API_KEY")
    print("flow_api_key: ", flow_api_key)
    if not flow_api_key:
        logging.warning("Environment variable FLOW_API_KEY not set. API key header will not be sent.")

    threads = []
    for _, row in bot_configs.iterrows():
        thread = threading.Thread(
            target=start_bot,
            args=(row['name'], row['bot_token'], row['app_token'], row['ping_url'], flow_api_key)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
