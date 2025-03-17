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
def handle_mention(body, say, client):
    # Extract the event data from the body
    event = body.get("event", {})
    
    # Check if this message is part of a thread
    thread_ts = event.get("thread_ts")
    thread_history = []
    
    # If it's in a thread, fetch the thread history
    if thread_ts:
        try:
            # Get the thread history
            thread_response = client.conversations_replies(
                channel=event["channel"],
                ts=thread_ts
            )
            if thread_response["ok"]:
                thread_history = thread_response["messages"]
        except Exception as e:
            print(f"Error fetching thread history: {str(e)}")
    
    # Define the API endpoint
    api_url = "https://6daa-2600-1700-420-354f-1434-30ca-3f3d-a54b.ngrok-free.app/api/v1/webhook/401e9b89-d2ab-4768-828f-10f641e6bcd8"
    
    # Prepare the payload with thread history
    payload = {
        "event": event,
        "thread_history": thread_history
    }

    # Send the event and thread history to the API endpoint
    try:
        response = requests.post(
            api_url,
            headers={
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        # Check if the request was successful
        if response.status_code == 202:
            print("Event and thread history sent to API successfully")
        else:
            say(f"Sorry, there was an error sending the event to the API: {response.status_code}")
        
    except Exception as e:
        say(f"Sorry, couldn't send the event to the API: {str(e)}")

# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 8000)))