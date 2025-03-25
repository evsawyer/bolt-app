import os
import requests
import pandas as pd
import threading
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define bot configurations in a DataFrame
bot_configs = pd.DataFrame([
    {
        "name": "DummyBot",
        "bot_token": os.environ.get("DUMMY_BOT_TOKEN"),
        "app_token": os.environ.get("DUMMY_APP_TOKEN"),
        "ping_url": "http://127.0.0.1:7866/api/v1/run/73bead24-6153-45d8-a3df-80abffd0133f?stream=false"
    },
    {
        "name": "DummyBot2",
        "bot_token": os.environ.get("DUMMY_BOT2_TOKEN"),
        "app_token": os.environ.get("DUMMY_APP2_TOKEN"),
        "ping_url": "http://127.0.0.1:7866/api/v1/run/595fb00d-675f-49e4-8283-ff9ec4fc40d7?stream=false"
    }
])

def process_events(client: SocketModeClient, req: SocketModeRequest, ping_url: str):
    # Acknowledge the request
    response = SocketModeResponse(envelope_id=req.envelope_id)
    client.send_socket_mode_response(response)

    # Extract the message from the payload
    event = req.payload.get("event", {})
    message_text = event.get("text", "")

    data = {
        "input_value": message_text,
        "output_type": "text",
        "input_type": "text"
        }
    print("DATA: ", data)
    # Forward the event data to the ping URL
    try:
        response = requests.post(
            ping_url,
            headers={"Content-Type": "application/json"},
            json=data,  # Send the modified payload
            timeout=5
        )
        if response.status_code >= 200 and response.status_code < 300:
            print("Successfully forwarded event")
        else:
            print(f"Failed to forward event. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error forwarding event: {str(e)}")

def start_bot(bot_name, bot_token, app_token, ping_url):
    if not bot_token or not app_token:
        print(f"Error: Tokens are required for {bot_name}")
        return

    client = WebClient(token=bot_token)
    socket_mode_client = SocketModeClient(
        app_token=app_token,
        web_client=client
    )

    # Add a listener for events
    socket_mode_client.socket_mode_request_listeners.append(
        lambda client, req: process_events(client, req, ping_url)
    )

    print(f"Info: Starting {bot_name} in Socket Mode!")
    socket_mode_client.connect()

if __name__ == "__main__":
    threads = []
    for _, row in bot_configs.iterrows():
        thread = threading.Thread(target=start_bot, args=(row['name'], row['bot_token'], row['app_token'], row['ping_url']))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()