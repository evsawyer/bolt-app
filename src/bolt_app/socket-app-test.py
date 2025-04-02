import os
import json
import pandas as pd
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from dotenv import load_dotenv
import logging
import traceback
import asyncio
import signal

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Define Bot Configurations ---
bot_configs = pd.DataFrame([
    {
        "name": "AsyncDummyBot",
        "bot_token": os.environ.get("DUMMY_BOT_TOKEN"),
        "app_token": os.environ.get("DUMMY_APP_TOKEN"),
    },
    # Add more bot configurations here if desired
    # Make sure they have unique names and corresponding ENV VARS
    # {
    #     "name": "AsyncDummyBot2",
    #     "bot_token": os.environ.get("DUMMY_BOT2_TOKEN"),
    #     "app_token": os.environ.get("DUMMY_APP2_TOKEN"),
    # },
])

# --- List to keep track of running handler tasks ---
running_bot_tasks = []

# --- Async Bot Task Function ---
async def start_async_bot(bot_name, bot_token, app_token):
    """Initializes and starts a single bot instance using AsyncIO."""
    logger = logging.getLogger(f"{__name__}.{bot_name}")
    handler = None # Initialize handler variable

    try:
        if not bot_token or not app_token:
            logger.error(f"Tokens required for {bot_name}, cannot start.")
            return

        # --- Use AsyncApp ---
        app = AsyncApp(token=bot_token)

        # --- Middleware must be async ---
        @app.middleware
        async def log_request_payload(body, next):
            logger.debug(f"****** Processing Incoming Payload ******")
            try:
                payload_str = json.dumps(body, indent=2)
                logger.debug(f"Payload Content:\n{payload_str}")
            except Exception as e:
                logger.error(f"Failed to dump payload to JSON: {e}")
                logger.debug(f"Raw Payload Body: {body}")
            await next() # Use await for next()

        # --- Event handlers must be async ---
        @app.event("app_mention")
        async def handle_app_mention(body, say): # logger is automatically available via app context
            logger.info(f"Entered handle_app_mention.")
            event = body.get("event", {})
            user = event.get("user", "someone")
            text = event.get("text", "_no text_")
            channel_id = event.get("channel")

            if channel_id:
                try:
                    response_text = f"Hi <@{user}>! I ({bot_name}) received your async 'app_mention' in channel `{channel_id}`. Text: `{text}`"
                    # --- 'say' returns an awaitable API response ---
                    await say(text=response_text, channel=channel_id)
                    logger.info(f"Sent app_mention acknowledgement to {channel_id}")
                except Exception as e:
                    logger.error(f"Failed to send acknowledgement message: {e}")
                    logger.error(traceback.format_exc())
            else:
                logger.warning(f"Could not determine channel ID for app_mention event.")

        # --- Other handlers also async ---
        @app.event("message")
        async def handle_message_ignore():
            logger.debug(f"Received message event (ignoring).")
            pass

        @app.event("reaction_added")
        async def handle_reaction_added(body, say):
             logger.info(f"Reaction added event received for {bot_name}")
             event = body.get("event", {})
             user = event.get("user", "someone")
             reaction = event.get("reaction", "_unknown_")
             item = event.get("item", {})
             channel_id = item.get("channel")
             if channel_id:
                try:
                    response_text = f"Thanks <@{user}>! I ({bot_name}) saw the async :{reaction}: reaction added in channel `{channel_id}`."
                    await say(text=response_text, channel=channel_id)
                    logger.info(f"Sent reaction_added acknowledgement to {channel_id}")
                except Exception as e:
                    logger.error(f"Failed to send message for reaction_added: {e}")
                    logger.error(traceback.format_exc())

        @app.event("reaction_removed")
        async def handle_reaction_removed(body, say):
             logger.info(f"Reaction removed event received for {bot_name}")
             event = body.get("event", {})
             user = event.get("user", "someone")
             reaction = event.get("reaction", "_unknown_")
             item = event.get("item", {})
             channel_id = item.get("channel")
             if channel_id:
                try:
                    response_text = f"Okay <@{user}>, I ({bot_name}) saw the async :{reaction}: reaction removed in channel `{channel_id}`."
                    await say(text=response_text, channel=channel_id)
                    logger.info(f"Sent reaction_removed acknowledgement to {channel_id}")
                except Exception as e:
                    logger.error(f"Failed to send message for reaction_removed: {e}")
                    logger.error(traceback.format_exc())


        # --- Error handler async ---
        @app.error
        async def handle_errors(error, body):
            logger.error(f"Uncaught Bolt Error: {error}")
            # ... (error logging) ...
            logger.error(traceback.format_exc())

        # --- Use AsyncSocketModeHandler ---
        handler = AsyncSocketModeHandler(app, app_token)
        logger.info(f"Starting {bot_name} asynchronously...")
        # --- Use await handler.start_async() ---
        await handler.start_async()
        # This line is reached when the handler is stopped

    except asyncio.CancelledError:
        logger.info(f"Task for {bot_name} received cancellation request.")
    except Exception as e:
        logger.error(f"Exception in start_async_bot for {bot_name}: {e}")
        logger.error(traceback.format_exc())
    finally:
        logger.info(f"Stopping handler for {bot_name}...")
        if handler and handler.client and handler.client.is_connected():
             await handler.close_async() # Use async close
             logger.info(f"Closed connection for {bot_name}")
        logger.info(f"Stopped {bot_name}.")


# --- Main Async Function ---
async def main():
    """Sets up signal handling and runs bot tasks."""
    main_logger = logging.getLogger(__name__)

    # --- Graceful Shutdown Handling for AsyncIO ---
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def shutdown_handler():
        main_logger.info("Shutdown signal received!")
        stop_event.set() # Signal the main loop to stop

    # Add signal handlers for SIGINT (Ctrl+C) and SIGTERM
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler for SIGTERM well
            main_logger.warning(f"Could not add signal handler for {sig.name} on this OS.")


    if bot_configs.empty:
        main_logger.error("No bot configurations found. Exiting.")
        return # Use return in async func

    main_logger.info(f"Found {len(bot_configs)} bot configurations to start.")

    # Create tasks for each bot
    for index, row in bot_configs.iterrows():
        bot_name = row.get("name")
        bot_token = row.get("bot_token")
        app_token = row.get("app_token")

        if not bot_name or not bot_token or not app_token:
            main_logger.warning(f"Skipping row {index} due to missing name/token: {row.to_dict()}")
            continue

        main_logger.info(f"Creating task for bot: {bot_name}")
        task = asyncio.create_task(
            start_async_bot(bot_name, bot_token, app_token),
            name=bot_name # Assign name to task for easier identification
        )
        running_bot_tasks.append(task)

    main_logger.info("All bot tasks created. Waiting for shutdown signal...")

    # Wait until shutdown signal is received
    await stop_event.wait()

    # --- Initiate Task Cancellation ---
    main_logger.info("Initiating cancellation of running tasks...")
    for task in running_bot_tasks:
        if not task.done():
            task.cancel()

    # Wait for tasks to finish cancellation (with a timeout)
    main_logger.info("Waiting for tasks to complete cancellation (up to 10 seconds)...")
    # Allow exceptions to propagate here to see cancellation errors if any
    await asyncio.wait(running_bot_tasks, timeout=10.0) # wait is simpler than gather for this

    # Check which tasks might not have finished cancelling cleanly
    remaining_tasks = [task for task in running_bot_tasks if not task.done()]
    if remaining_tasks:
        main_logger.warning(f"{len(remaining_tasks)} task(s) did not finish cleanly:")
        for task in remaining_tasks:
             main_logger.warning(f"  - Task: {task.get_name()}") # Requires Python 3.8+ for get_name

    main_logger.info("Async main finished.")


# --- Run the main async function ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This might still catch Ctrl+C if signal handlers aren't setup/working perfectly
        logging.getLogger(__name__).info("Main KeyboardInterrupt caught (graceful shutdown via signal handler preferred).")
