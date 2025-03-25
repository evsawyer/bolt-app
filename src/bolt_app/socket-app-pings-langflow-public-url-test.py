import os
import requests
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import threading

# Load environment variables
load_dotenv()

# Initialize the Slack app
DummyBot = App(token=os.environ.get("DUMMY_BOT_TOKEN"))
DummyBot2 = App(token=os.environ.get("DUMMY_BOT2_TOKEN"))
# URL to ping when a message is received
DUMMY_BOT_PING_URL = "http://127.0.0.1:7866/api/v1/run/73bead24-6153-45d8-a3df-80abffd0133f?stream=false"

DUMMY_BOT2_PING_URL = "http://127.0.0.1:7866/api/v1/run/595fb00d-675f-49e4-8283-ff9ec4fc40d7?stream=false"

@DummyBot.event("app_mention")
def handle_message_events_dummy_bot(body, logger):
    """
    Handle message events for DummyBot.
    When a message is received, ping the specified URL with the entire body.
    """
    # Get the message event from the body
    event = body.get("event", {})
    # print("EVENT: ", event)

    # Extract message info for logging only
    message_text = event.get("text", "")
    channel = event.get("channel")
    user = event.get("user", "Unknown")
    # Data payload
    data = {
        "input_value": message_text,
        "output_type": "text",
        "input_type": "text",
        "tweaks": {
            "Agent-tBKKO": {},
            "TextInput-vbFr1": {},
            "TextOutput-bUkDD": {}
        }
    }

    print(f"Info: Received message from user {user} in channel {channel}: {message_text}")
    print("Info: Sending message to DummyBot")
    
    try:
        # Ping the URL with the entire body data
        print(f"Info: Pinging URL: {DUMMY_BOT_PING_URL}")
        print(f"Info: Sending entire body without preprocessing")
        

        response = requests.post(
            DUMMY_BOT_PING_URL,
            headers={"Content-Type": "application/json"},
            json=data,  # Send the entire body without modification
            timeout=5   # Short timeout since we just need to ping
        )
        
        print(f"Info: Ping response status: {response.status_code}")
        
        if response.status_code >= 200 and response.status_code < 300:
            print("Info: Successfully pinged URL")
        else:
            print(f"Error: Failed to ping URL. Status code: {response.status_code}")
    
    except Exception as e:
        print(f"Error: Exception while pinging URL: {str(e)}")

@DummyBot2.event("app_mention")
def handle_message_events_dummy_bot2(body, logger):
    """
    Handle message events for DummyBot2.
    When a message is received, ping the specified URL with the entire body.
    """
    # Get the message event from the body
    event = body.get("event", {})

    print("EVENT: ", event)
    # Extract message info for logging only
    message_text = event.get("text", "")
    channel = event.get("channel")
    user = event.get("user", "Unknown")

    # Data payload
    data = {
        "input_value": message_text,
        "output_type": "text",
        "input_type": "text",
        "tweaks": {
            "Agent-tBKKO": {},
            "TextInput-vbFr1": {},
            "TextOutput-bUkDD": {}
        }
    }
    print("DATA: ", data)

    payload = data
    
    print(f"Info: Received message from user {user} in channel {channel}: {message_text}")
    print("Info: Sending message to DummyBot2")
    
    try:
        # Ping the URL with the entire body data
        print(f"Info: Pinging URL: {DUMMY_BOT2_PING_URL}")
        print(f"Info: Sending entire body without preprocessing")
        
        response = requests.post(
            DUMMY_BOT2_PING_URL,
            headers={"Content-Type": "application/json"},
            json=payload,  # Send the entire body without modification
            timeout=5   # Short timeout since we just need to ping
        )
        
        print(f"Info: Ping response status: {response.status_code}")
        
        if response.status_code >= 200 and response.status_code < 300:
            print("Info: Successfully pinged URL")
        else:
            print(f"Error: Failed to ping URL. Status code: {response.status_code}")
    
    except Exception as e:
        print(f"Error: Exception while pinging URL: {str(e)}")

def start_bot(bot_name, bot_token, app_token, ping_url):
    if not bot_token or not app_token:
        print(f"Error: Tokens are required for {bot_name}")
        return

    app = App(token=bot_token)

    @app.event("app_mention")
    def handle_message_events(body, logger):
        event = body.get("event", {})
        message_text = event.get("text", "")
        channel = event.get("channel")
        user = event.get("user", "Unknown")

        data = {
            "input_value": message_text,
            "output_type": "text",
            "input_type": "text",
            "tweaks": {
                "Agent-tBKKO": {},
                "TextInput-vbFr1": {},
                "TextOutput-bUkDD": {}
            }
        }

        print(f"Info: Received message from user {user} in channel {channel}: {message_text}")
        print(f"Info: Sending message to {bot_name}")

        try:
            response = requests.post(
                ping_url,
                headers={"Content-Type": "application/json"},
                json=data,
                timeout=5
            )

            print(f"Info: Ping response status: {response.status_code}")

            if response.status_code >= 200 and response.status_code < 300:
                print("Info: Successfully pinged URL")
            else:
                print(f"Error: Failed to ping URL. Status code: {response.status_code}")

        except Exception as e:
            print(f"Error: Exception while pinging URL: {str(e)}")

    print(f"Info: Starting {bot_name} in Socket Mode!")
    handler = SocketModeHandler(app, app_token)
    handler.start()

def start_dummy_bot():
    dummy_app_token = os.environ.get("DUMMY_APP_TOKEN")
    if not dummy_app_token:
        print("Error: DUMMY_APP_TOKEN environment variable is required for Socket Mode for DummyBot")
        return
    print("Info: Starting DummyBot in Socket Mode!")
    handler_1 = SocketModeHandler(DummyBot, dummy_app_token)
    handler_1.start()

def start_dummy_bot2():
    dummy2_app_token = os.environ.get("DUMMY_APP2_TOKEN")
    if not dummy2_app_token:
        print("Error: DUMMY_APP2_TOKEN environment variable is required for Socket Mode for DummyBot2")
        return
    print("Info: Starting DummyBot2 in Socket Mode!")
    handler_2 = SocketModeHandler(DummyBot2, dummy2_app_token)
    handler_2.start()

if __name__ == "__main__":
    # Create threads for each bot
    thread_1 = threading.Thread(target=start_dummy_bot)
    thread_2 = threading.Thread(target=start_dummy_bot2)

    # Start the threads
    thread_1.start()
    thread_2.start()

    # # Join the threads to ensure they run concurrently
    thread_1.join()
    thread_2.join()
    
    
