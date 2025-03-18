# Slack Bot with Socket Mode and Webhook Integration

A Slack bot that uses Socket Mode to connect to Slack and forwards event payloads to a webhook endpoint for processing.

## Features

- Uses Socket Mode to connect to Slack without exposing public endpoints
- Forwards message events to a local webhook for processing
- Captures thread history for context in ongoing conversations
- Sends webhook responses back to the Slack thread

## Requirements

- Python 3.13+
- Poetry for dependency management
- A Slack app with Socket Mode enabled

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SOCKET_TOKEN=xapp-your-app-token
```

## Setup Instructions

1. **Create a Slack App**
   - Go to [https://api.slack.com/apps](https://api.slack.com/apps)
   - Click "Create New App" and choose "From scratch"
   - Name your app and select your workspace
   - Under "Socket Mode", enable it and generate an app-level token (starts with xapp-)
   - Under "Event Subscriptions", enable events and subscribe to the "message.channels" bot event
   - Under "OAuth & Permissions", add the following bot scopes:
     - `app_mentions:read`
     - `channels:history`
     - `chat:write`
     - `im:history`
     - `im:write`
   - Install the app to your workspace
   - Copy the Bot User OAuth Token (starts with xoxb-)

2. **Install Dependencies**
   ```bash
   poetry install
   ```

3. **Configure Webhook Endpoint**
   - The app is configured to send event payloads to: `http://127.0.0.1:7866/api/v1/webhook/8c2fba5b-85af-450b-bb4f-34c53fcb5679`
   - Make sure your webhook server is running at this address
   - The webhook should accept POST requests with JSON payloads
   - For custom webhook URLs, modify the `WEBHOOK_URL` constant in the code

## Running the Bot

```bash
poetry run python src/bolt_app/socket-app.py
```

## How It Works

1. The bot listens for any messages sent in channels it's invited to
2. When it receives a message, it checks if it's part of a thread and fetches thread history if needed
3. It constructs a payload with the event data and thread history
4. The payload is sent to the webhook endpoint
5. The bot sends the webhook's response back to the Slack thread

## Payload Format

The webhook receives a JSON payload with the following structure:

```json
{
  "event": {
    "type": "message",
    "user": "U12345678",
    "text": "Hello world",
    "channel": "C12345678",
    "ts": "1234567890.123456",
    "thread_ts": "1234567890.123456"  // Only present if in a thread
  },
  "thread_history": [  // Only present if message is in a thread
    {
      "user": "<@U12345678>",
      "text": "Previous message",
      "ts": "1234567890.123456"
    },
    // More messages...
  ]
}
```

## Response Format

The webhook can return a JSON response with a "response" field to specify the message to send back to Slack:

```json
{
  "response": "This will be sent back to the Slack thread"
}
```

## Troubleshooting

- Make sure your app has been invited to the channels where you want it to work
- Check that all required environment variables are set correctly
- Ensure your webhook server is running and accessible at the specified URL
- Verify that Socket Mode is enabled in your Slack app
