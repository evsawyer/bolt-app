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
WEBHOOK_URL = "http://127.0.0.1:7866/api/v1/webhook/8c2fba5b-85af-450b-bb4f-34c53fcb5679"

@app.event("message")
def handle_message_events(body, say, logger):
    """
    Handle message events in Slack channels.
    Only respond to messages that don't come from a bot.
    """
    # Get the message event from the body
    event = body.get("event", {})
    
    # Skip messages from bots to avoid potential infinite loops
    if event.get("bot_id"):
        return
    
    # Extract message text and channel
    message_text = event.get("text", "")
    channel = event.get("channel")
    thread_ts = event.get("thread_ts", event.get("ts"))  # Use thread_ts if available, otherwise use message ts
    
    # Log the incoming message
    user = event.get("user", "Unknown")
    logger.info(f"Received message from user {user} in channel {channel}: {message_text}")
    
    # Check if message is in a thread
    thread_history = []
    if thread_ts and thread_ts != event.get("ts"):
        try:
            # Get the thread history
            client = app.client
            thread_response = client.conversations_replies(
                channel=channel,
                ts=thread_ts
            )
            
            if thread_response["ok"]:
                # Extract essential information from messages
                raw_messages = thread_response["messages"][-5:]  # Limit to last 5 messages
                for msg in raw_messages:
                    user_info = "Bot" if msg.get("bot_id") else f"<@{msg.get('user')}>"
                    thread_history.append({
                        "user": user_info,
                        "text": msg.get("text", ""),
                        "ts": msg.get("ts")
                    })
                logger.info(f"Retrieved {len(thread_history)} messages from thread history")
        except Exception as e:
            logger.error(f"Error retrieving thread history: {str(e)}")
    
    # Prepare payload for webhook
    payload = {
        "event": event,
        "thread_history": thread_history
    }
    
    try:
        # Forward the event payload to the webhook
        logger.info(f"Forwarding event payload to webhook: {WEBHOOK_URL}")
        
        response = requests.post(
            WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10  # Add timeout to prevent hanging
        )
        
        logger.info(f"Webhook response status: {response.status_code}")
        
        if response.status_code == 202:
            try:
                # Try to parse response as JSON
                webhook_response = response.json()
                if "response" in webhook_response:
                    # If webhook returns a response message, send it to Slack
                    say(text=webhook_response["response"], thread_ts=thread_ts)
                    logger.info("Sent webhook response back to Slack")
                else:
                    # No specific response found, send generic confirmation
                    say(text="Your message was received and processed.", thread_ts=thread_ts)
            except json.JSONDecodeError:
                # If response is not JSON, just send the raw text if it's not too long
                if len(response.text) < 1000:
                    say(text=response.text, thread_ts=thread_ts)
                else:
                    say(text="Received response from webhook (too large to display here).", thread_ts=thread_ts)
        else:
            # Error handling for non-200 responses
            say(text=f"Error processing request. Status code: {response.status_code}", thread_ts=thread_ts)
            logger.error(f"Webhook error response: {response.text[:500]}")
    
    except Exception as e:
        logger.error(f"Error forwarding to webhook: {str(e)}")
        say(text=f"Sorry, I encountered an error: {str(e)}", thread_ts=thread_ts)

if __name__ == "__main__":
    # Start the Socket Mode handler
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    print("⚡️ Bolt app is running in Socket Mode!")
    handler.start()
