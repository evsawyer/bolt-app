import os
import json
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
    # Print the full body for debugging
    print("\n=== FULL EVENT BODY ===")
    print(f"Type: {type(body)}")
    print(f"Keys: {body.keys() if isinstance(body, dict) else 'Not a dict'}")
    print("=======================\n")
    
    # Extract the event data from the body
    event = body.get("event", {})
    
    # Print event details
    print("=== EVENT DETAILS ===")
    print(f"Event type: {event.get('type')}")
    print(f"Event user: {event.get('user')}")
    print(f"Event text: {event.get('text')}")
    print(f"Event channel: {event.get('channel')}")
    print(f"Event thread_ts: {event.get('thread_ts')}")
    print(f"Event ts: {event.get('ts')}")
    print("=====================\n")
    
    # Check if this message is part of a thread
    thread_ts = event.get("thread_ts")
    thread_history = []
    
    # If it's in a thread, fetch the thread history
    if thread_ts:
        try:
            print(f"=== FETCHING THREAD HISTORY ===")
            print(f"Thread ts: {thread_ts}")
            print(f"Channel: {event.get('channel')}")
            
            # Get the thread history
            thread_response = client.conversations_replies(
                channel=event["channel"],
                ts=thread_ts
            )
            
            print(f"Thread response OK: {thread_response.get('ok')}")
            print(f"Thread response has messages: {'messages' in thread_response}")
            print(f"Message count: {len(thread_response.get('messages', []))}")
            print("=============================\n")
            
            # Limit thread history to only the most recent 5 messages
            raw_messages = thread_response["messages"][-5:] if thread_response["ok"] else []
            
            # Extract just the essential information from each message
            thread_history = []
            for msg in raw_messages:
                # Get user info - either the real name or the user ID
                user_info = "Bot" if msg.get("bot_id") else f"<@{msg.get('user')}>"
                
                thread_history.append({
                    "user": user_info,
                    "text": msg.get("text", ""),
                    "ts": msg.get("ts")
                })
            
            # Print summary of thread history
            print("=== THREAD HISTORY SUMMARY ===")
            for i, msg in enumerate(thread_history):
                print(f"Message {i+1}:")
                print(f"  User: {msg.get('user')}")
                print(f"  Text: {msg.get('text')[:100]}..." if len(msg.get('text', '')) > 100 else f"  Text: {msg.get('text')}")
                print(f"  Timestamp: {msg.get('ts')}")
            print("=============================\n")
        except Exception as e:
            print(f"Error fetching thread history: {str(e)}")
            print(f"Exception type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    
    # Define the API endpoint
    api_url = "https://05ec-2600-1700-420-354f-dd5f-f782-279b-810f.ngrok-free.app/api/v1/webhook/55d380d6-5107-4ed9-b7be-fcd82f053f1a"
    
    # Prepare the payload with thread history
    payload = {
        "event": event,
        "thread_history": thread_history
    }
    
    # Print the payload we're about to send
    print("=== PAYLOAD BEING SENT ===")
    print(f"Payload type: {type(payload)}")
    print(f"Payload keys: {payload.keys()}")
    print(f"Event in payload: {bool(payload.get('event'))}")
    print(f"Thread history in payload: {bool(payload.get('thread_history'))}")
    print(f"Thread history length: {len(payload.get('thread_history', []))}")
    
    # Print a serialized version of the payload to check for JSON issues
    try:
        serialized = json.dumps(payload)
        print(f"Successfully serialized payload to JSON (length: {len(serialized)})")
    except Exception as e:
        print(f"Error serializing payload: {str(e)}")
    print("=========================\n")

    # Send the event and thread history to the API endpoint
    try:
        print(f"=== SENDING REQUEST TO API ===")
        print(f"API URL: {api_url}")
        
        response = requests.post(
            api_url,
            headers={
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        # Print response details
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response content: {response.text[:200]}..." if len(response.text) > 200 else f"Response content: {response.text}")
        print("============================\n")
        
        # Check if the request was successful
        if response.status_code == 202:
            print("Event and thread history sent to API successfully")
        else:
            print(f"Error sending to API: Status code {response.status_code}")
            say(f"Sorry, there was an error sending the event to the API: {response.status_code}")
        
    except Exception as e:
        print(f"Exception sending request: {str(e)}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        say(f"Sorry, couldn't send the event to the API: {str(e)}")

# Start your app
if __name__ == "__main__":
    print("\n=== STARTING SLACK APP ===")
    print(f"SLACK_BOT_TOKEN: {'Set' if os.environ.get('SLACK_BOT_TOKEN') else 'Not Set'}")
    print(f"SLACK_SIGNING_SECRET: {'Set' if os.environ.get('SLACK_SIGNING_SECRET') else 'Not Set'}")
    print("=========================\n")
    
    app.start(port=int(os.environ.get("PORT", 8000)))