import os
import logging
import traceback
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variable names for the test bot
BOT_TOKEN_ENV_VAR = "DUMMY_BOT_TOKEN"
APP_TOKEN_ENV_VAR = "DUMMY_APP_TOKEN"
BOT_NAME = "SimpleTestBot"

def start_simple_bot(bot_name, bot_token, app_token):
    """Initializes and starts a simple Slack bot using Socket Mode."""
    if not bot_token:
        logger.error(f"'{BOT_TOKEN_ENV_VAR}' environment variable not set. Cannot start {bot_name}.")
        return
    if not app_token:
        logger.error(f"'{APP_TOKEN_ENV_VAR}' environment variable not set. Cannot start {bot_name}.")
        return

    # Initialize Bolt app
    app = App(token=bot_token)

    @app.event("app_mention")
    def handle_app_mention(body, say, event_logger):
        """Handles app mention events by logging the bot's name."""
        # The logger passed by Bolt is named 'event_logger' here to avoid conflict
        event_logger.info(f"App mentioned! This is {bot_name}.")
        print(f"Info: App mentioned! This is {bot_name}.")
        # Optionally, you could add a simple reply:
        # user = body.get("event", {}).get("user")
        # try:
        #     say(f"Hi there, <@{user}>! I'm {bot_name}.")
        # except Exception as e:
        #     event_logger.error(f"Error sending reply: {e}")

    # Start the Socket Mode handler
    logger.info(f"Attempting to start {bot_name} in Socket Mode...")
    try:
        handler = SocketModeHandler(app, app_token)
        handler.start()  # This blocks the thread execution
    except Exception as e:
        logger.error(f"Error starting Socket Mode handler for {bot_name}: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Retrieve tokens from environment variables
    test_bot_token = os.environ.get("DUMMY_BOT_TOKEN")
    test_app_token = os.environ.get("DUMMY_APP_TOKEN")

    # Start the bot if tokens are found
    if test_bot_token and test_app_token:
        start_simple_bot(BOT_NAME, test_bot_token, test_app_token)
    else:
        logger.error(f"Required environment variables ('{BOT_TOKEN_ENV_VAR}', '{APP_TOKEN_ENV_VAR}') not found. Exiting.")
