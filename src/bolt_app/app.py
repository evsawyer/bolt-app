import os
from slack_bolt import App
from dotenv import load_dotenv
import logging
#test
load_dotenv()
# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the log level to INFO
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler()  # Output logs to the console
    ]
)

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
# print the tail of the slack bot token and the slack signing secret
print(os.environ.get("SLACK_BOT_TOKEN")[-5:])
print(os.environ.get("SLACK_SIGNING_SECRET")[-5:])
# Listens to incoming messages that contain "hello"
# To learn available listener arguments,
# visit https://tools.slack.dev/bolt-python/api-docs/slack_bolt/kwargs_injection/args.html
@app.message("hello")
def message_hello(message, say):
    print(message)
    # say() sends a message to the channel where the event was triggered
    say(f"Hey there <@{message['user']}>!", thread_ts=message['ts'])

@app.event("reaction_added")
def handle_reaction_added_events(body, logger):
    logger.info(body)
# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get(8000)))