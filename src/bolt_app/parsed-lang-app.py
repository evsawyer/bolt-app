import os
import json
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# URL to forward events to
FORWARD_URL = os.environ.get("FORWARD_URL", "https://example.com/webhook")

def forward_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Forward the event payload to the specified URL.
    Returns the response from the forwarded request.
    """
    try:
        logger.info(f"Forwarding event to {FORWARD_URL}")
        logger.info(f"Payload keys: {list(payload.keys())}")
        
        response = requests.post(
            FORWARD_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10
        )
        
        logger.info(f"Response status code: {response.status_code}")
        
        # Try to parse response as JSON
        try:
            response_data = response.json()
            logger.info(f"Response JSON: {json.dumps(response_data)[:500]}...")
            return response_data
        except json.JSONDecodeError:
            logger.info(f"Response text: {response.text[:500]}...")
            return {"text": response.text}
            
    except Exception as e:
        logger.error(f"Error forwarding event: {str(e)}")
        return {"error": str(e)}

# Special handler for URL verification challenges
@app.event("url_verification")
def handle_verification(body):
    logger.info("Received URL verification challenge")
    return {"challenge": body.get("challenge")}

# Global event handler that will catch all events
@app.event({"type": ".*"})
def handle_all_events(body, logger):
    """
    Catch-all handler for any event type.
    Forwards the full event payload to the specified URL.
    """
    event_type = body.get("event", {}).get("type", "unknown")
    logger.info(f"Received event of type: {event_type}")
    
    # Forward the event and get response
    response = forward_event(body)
    
    # Log completion
    logger.info(f"Event {event_type} forwarded successfully")
    return response

# Message event handler - this will catch all messages
@app.event("message")
def handle_message_events(body, say, logger):
    """
    Handle message events specifically.
    This gives us the ability to reply in the channel if needed.
    """
    logger.info("Received message event")
    
    # Forward the event
    response = forward_event(body)
    
    # Check if we need to say something back in the channel
    if response and "slack_response" in response:
        event = body.get("event", {})
        channel = event.get("channel")
        thread_ts = event.get("thread_ts", event.get("ts"))
        
        # Say the response in the channel
        say(text=response["slack_response"], thread_ts=thread_ts)
        logger.info(f"Replied in channel {channel} with response from webhook")

# App mention handler
@app.event("app_mention")
def handle_app_mention(body, say, logger):
    """
    Handle app mention events.
    """
    logger.info("Received app_mention event")
    
    # Forward the event
    response = forward_event(body)
    
    # Check if we need to say something back in the channel
    if response and "slack_response" in response:
        event = body.get("event", {})
        channel = event.get("channel")
        thread_ts = event.get("thread_ts", event.get("ts"))
        
        # Say the response in the channel
        say(text=response["slack_response"], thread_ts=thread_ts)
        logger.info(f"Replied to mention in channel {channel}")

# Handle errors
@app.error
def handle_errors(error, body, logger):
    logger.error(f"Error: {error}")
    logger.error(f"Request body: {body}")

if __name__ == "__main__":
    # Check if we're using Socket Mode or HTTP
    if os.environ.get("SOCKET_MODE", "false").lower() == "true":
        # Start in Socket Mode
        socket_token = os.environ.get("SOCKET_TOKEN") or os.environ.get("SLACK_APP_TOKEN")
        if not socket_token:
            logger.error("SOCKET_TOKEN or SLACK_APP_TOKEN environment variable is required for Socket Mode")
            exit(1)
            
        logger.info("Starting app in Socket Mode")
        handler = SocketModeHandler(app, socket_token)
        handler.start()
    else:
        # Start with HTTP server
        port = int(os.environ.get("PORT", 3000))
        logger.info(f"Starting HTTP server on port {port}")
        app.start(port=port)
