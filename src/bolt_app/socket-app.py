import os
import json
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Slack app
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Define the webhook URL
WEBHOOK_URL = "http://127.0.0.1:7866/api/v1/webhook/197bb78f-511f-49d2-911c-38c7c767f449"

@app.event("message")
def handle_message_events(body, logger):
    """
    Handle message events in Slack channels.
    Only respond to messages that don't come from a bot.
    Simply forward them to the webhook URL.
    """
    # Get the message event from the body
    event = body.get("event", {})
    
    # Skip messages from bots to avoid potential infinite loops
    if event.get("bot_id"):
        return
    
    # Extract message text and channel
    message_text = event.get("text", "")
    channel = event.get("channel")
    thread_ts = event.get("thread_ts")  # Use thread_ts if available, otherwise use message ts
    
    # Log the incoming message
    user = event.get("user", "Unknown")
    print(f"Info: Received message from user {user} in channel {channel}: {message_text}")
    print(f"Info: Thread timestamp: {thread_ts}, Message timestamp: {event.get('ts')}")
    
    # Check if message is in a thread
    thread_history = []
    if thread_ts:
        try:
            # Get the thread history
            client = app.client
            thread_response = client.conversations_replies(
                channel=channel,
                ts=thread_ts  # This is the parent thread timestamp
            )
            
            print(f"Info: Thread API response status: {thread_response.get('ok')}")
            print(f"Info: Number of messages in thread: {len(thread_response.get('messages', []))}")
            
            if thread_response["ok"]:
                # Extract essential information from messages
                # The responses from conversations_replies only includes messages from the specific thread
                raw_messages = thread_response["messages"]
                # Limit to most recent 5 messages to keep payload size reasonable
                raw_messages = raw_messages[-5:] if len(raw_messages) > 5 else raw_messages
                
                print(f"Info: Processing {len(raw_messages)} thread messages")
                
                for msg in raw_messages:
                    user_info = "Bot" if msg.get("bot_id") else f"<@{msg.get('user')}>"
                    thread_history.append({
                        "user": user_info,
                        "text": msg.get("text", ""),
                        "ts": msg.get("ts")
                    })
                    print(f"Info: Added message '{msg.get('text', '')[:30]}...' to thread history")
  
                print(f"Info: Retrieved {len(thread_history)} messages from thread history")
        except Exception as e:
            print(f"Error: Error retrieving thread history: {str(e)}")
    
    # Prepare payload for webhook
    payload = {
        "event": event,
        "thread_history": thread_history
    }
    
    try:
        # Forward the event payload to the webhook
        print(f"Info: Forwarding event payload to webhook: {WEBHOOK_URL}")
        print(f"Info: Payload: {json.dumps(payload)}")
        # print the thread history as well
        print(f"Info: Thread history: {thread_history}")
        
        response = requests.post(
            WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10  # Add timeout to prevent hanging
        )
        
        print(f"Info: Webhook response status: {response.status_code}")
        
        # Just log the response status, don't process or respond with it
        if response.status_code >= 200 and response.status_code < 300:
            print("Info: Successfully forwarded payload to webhook")
        else:
            print(f"Error: Failed to forward payload. Status code: {response.status_code}")
    
    except Exception as e:
        print(f"Error: Error forwarding to webhook: {str(e)}")

@app.error
def handle_errors(error, body):
    print(f"Error: {error}")
    print(f"Error: Request body: {body}")

if __name__ == "__main__":
    # Start the Socket Mode handler
    socket_token = os.environ.get("SLACK_APP_TOKEN")
    if not socket_token:
        print("Error: SLACK_APP_TOKEN environment variable is required for Socket Mode")
        exit(1)
        
    print("Info: Starting app in Socket Mode")
    handler = SocketModeHandler(app, socket_token)
    print("⚡️ Bolt app is running in Socket Mode!")
    handler.start()
