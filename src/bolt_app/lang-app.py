import os
import requests
from slack_bolt import App
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# When the bot is mentioned, send user text to API endpoint
@app.event("app_mention")
def handle_mention(body, say):
    # Extract the user's message (remove the bot mention)
    event = body.get("event", {})
    user_text = event["text"]
    
    # Define the API endpoint
    api_url = "https://c1e3-2600-1700-420-354f-1434-30ca-3f3d-a54b.ngrok-free.app/api/v1/webhook/55d380d6-5107-4ed9-b7be-fcd82f053f1a"  # Replace with your actual API endpoint
    
    # Send the message to the API endpoint
    try:
        response = requests.post(
            api_url,
            headers={
                "Content-Type": "application/json"
            },
            json={"text": user_text}
        )
        
        # Check if the request was successful
        if response.status_code == 202:
            say(f"I've sent your message to the API!")
        else:
            say(f"Sorry, there was an error sending your message to the API: {response.status_code}")
        
    except Exception as e:
        say(f"Sorry, couldn't send your message to the API: {str(e)}")

# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 8000)))