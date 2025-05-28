import os
import requests
import json
import threading
from slack_bolt import App
from dotenv import load_dotenv
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer # <-- Import HTTP server modules

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

flow_api_key = os.environ.get("FLOW_API_KEY")
bot_name = os.environ.get("BOT_NAME")
bot_token = os.environ.get("BOT_TOKEN")
ping_url = os.environ.get("PING_URL")

# custom local testing
# ping_url="https://langflow.ivc.media/api/v1/run/971042c4-c8a0-4889-a842-8a403a1d2a8b?stream=false"
# flow_api_key="sk-gP0BDYIKrkqqxmL_36kVtdPmmMIZMlimvbnQIwOcKTM"

#add checks that all these are indeed set
if not os.environ.get("FLOW_API_KEY"):
    logging.error("FLOW_API_KEY not set. Cannot start bot.")
    exit(1)
if not os.environ.get("BOT_NAME"):
    logging.error("BOT_NAME not set. Cannot start bot.")
    exit(1)
if not os.environ.get("BOT_TOKEN"):
    logging.error("BOT_TOKEN not set. Cannot start bot.")
    exit(1)
if not os.environ.get("PING_URL"):
    logging.error("PING_URL not set. Cannot start bot.")
    exit(1)

# --- Health Check Server ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Respond with 200 OK for any GET request
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_check_server(port):
    server_address = ('', port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    logging.info(f"Starting health check server on port {port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info(f"Stopped health check server on port {port}")
# --- End Health Check Server ---

def start_bot(bot_name, bot_token, ping_url, api_key):
    app = App(token=bot_token, raise_error_for_unhandled_request=True)

    @app.event("message")
    def handle_message_events(body, logger):
        pass

    @app.event("app_mention")  # Listen to app mention events
    def handle_app_mention_events(body, logger):
        logger.info(f"App mention event received for {bot_name}")
        event = body.get("event", {})
        # print the entire event
        print("=" * 40)
        print(f"📦 Incoming payload to app mention:")
        print(json.dumps(body, indent=2))
        print("=" * 40)

        channel_id = event.get("channel")
        # Get timestamps from the event
        ts = event.get("ts")
        thread_ts = event.get("thread_ts")
        session_id = str(channel_id + "-" + thread_ts if thread_ts else channel_id + "-" + ts)
        event_str = json.dumps(event)  # Convert event to a JSON string
        data = {
            "input_value": event_str,
            "input_type": "text",
            "output_type": "text",
            "session_id": session_id
        }
        try:
            forward_event(data, ping_url, api_key, bot_name)
        except Exception as e:
            logger.error(f"Error forwarding event for {bot_name}: {e}")

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
        forward_event(data, ping_url, api_key, bot_name)
    
    @app.error
    def handle_errors(error, body, logger):
        """Global error handler to catch and log errors, especially unhandled requests."""
        logger.error(f"({bot_name}) Uncaught error: {error}")
        logger.error(f"({bot_name}) Request body: {body}")

    health_check_port = 8080
    health_thread = threading.Thread(target=run_health_check_server, args=(health_check_port,), daemon=True)
    health_thread.start()

    print(f"Info: Starting {bot_name} in HTTP Mode!")
    try:
        app.start(port=int(os.environ.get("PORT", 8000)))
    except Exception as e:
        logging.error(f"Error starting app for {bot_name}: {e}")
    finally:
         # Optional: Could add logic here to signal the health check server to stop if needed
         pass
# Helper function to forward events
def forward_event(data, ping_url, api_key, bot_name):
    logging.info(f"forwarding the event to {bot_name}")
    logging.info(f"ping_url: {ping_url}")
    logging.info(f"api_key snippet: {api_key[-10:]}")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers['x-api-key'] = api_key
    else:
        logging.warning("FLOW_API_KEY not set. Proceeding without x-api-key header.")

    try:
        response = requests.post(
            ping_url,
            headers=headers,
            json=data,
            timeout=5
        )
        print("response: ", response)
        if response.status_code >= 200 and response.status_code < 300:
            logging.info("Info: Successfully pinged URL")
        else:
            logging.error(f"Failed to ping URL. Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        logging.warning(f"Exception while pinging URL: {str(e)}")

if __name__ == "__main__":
    print(f"Starting bot: {bot_name}")
    start_bot(
        bot_name=bot_name,
        bot_token=bot_token,
        ping_url=ping_url,
        api_key=flow_api_key
    )