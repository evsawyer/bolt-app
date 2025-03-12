import os
import logging
import requests
import openai
from dotenv import load_dotenv
from slack_bolt import App

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)
#test
# print the tail of the slack bot token and the slack singing secret
print(os.environ.get("SLACK_BOT_TOKEN")[-5:])
print(os.environ.get("SLACK_SIGNING_SECRET")[-5:])

# Initialize the Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)


# Initialize OpenAI client
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Function to get weather data from api.weather.gov
def get_weather(latitude, longitude):
    points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
    response = requests.get(points_url)
    
    if response.status_code == 200:
        points_data = response.json()
        forecast_url = points_data['properties']['forecast']
        forecast_response = requests.get(forecast_url)
        
        if forecast_response.status_code == 200:
            forecast_data = forecast_response.json()
            return forecast_data['properties']['periods'][0]
        else:
            logging.error(f"Failed to fetch forecast: {forecast_response.status_code} - {forecast_response.text}")
    else:
        logging.error(f"Failed to fetch grid points: {response.status_code} - {response.text}")
    return None

# Function to determine the intent of a message using ChatGPT
def gpt_intent(message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": """You are an AI assistant that analyzes messages to determine their intent.
                If the message is asking about weather, respond with a JSON object:
                {"intent": "weather", "location": "<location>", "time": "<time>"}
                
                If no location is provided, default to "University Heights, San Diego".
                If no time is specified, default to "today".
                
                For all other messages, respond with:
                {"intent": "chat"}
                
                Respond ONLY with the JSON object and nothing else."""},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error calling OpenAI API for intent determination: {e}")
        return '{"intent": "chat"}'

# Function to ask ChatGPT a question
def ask_chatgpt(question):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a gruff pirate with lots of thoughts about life as a pirate. You are helpful, but when answering a question, you always loop back to your life as a pirate."},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {e}")
        return "Sorry, I couldn't process your question at the moment."

# Function to get latitude and longitude from OpenStreetMap
def get_lat_lon(location):
    try:
        response = requests.get(f"https://nominatim.openstreetmap.org/search?q={location}&format=json")
        if response.status_code == 200 and response.json():
            return response.json()[0]['lat'], response.json()[0]['lon']
        else:
            logging.error(f"Failed to fetch location data: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error calling OpenStreetMap API: {e}")
    return "32.7481", "-117.1313"  # Default to University Heights, San Diego

# Listens for app_mention events
@app.event("app_mention")
def handle_app_mention_events(body, say):
    event = body.get("event", {})
    text = event.get("text", "").lower()
    user_message = text.replace(f"<@{event.get('bot_id', '')}>", "").strip()
    
    # First, determine the intent using gpt_intent
    intent_response = gpt_intent(user_message)
    logging.info(f"Intent response: {intent_response}")
    
    try:
        # Try to parse the JSON response
        import json
        intent_data = json.loads(intent_response)
    except Exception as e:
        logging.error(f"Error parsing intent response: {e}")
        say("Sorry, I couldn't understand your request.")
        return

    if intent_data.get("intent") == "weather":
        location = intent_data.get("location", "University Heights, San Diego")
        time = intent_data.get("time", "today")
        latitude, longitude = get_lat_lon(location)
        weather_data = get_weather(latitude, longitude)
        if weather_data:
            weather_message = (
                f"Weather in {location} for {time}:\n"
                f"Temperature: {weather_data['temperature']}°{weather_data['temperatureUnit']}\n"
                f"Wind: {weather_data['windSpeed']} from {weather_data['windDirection']}\n"
                f"Forecast: {weather_data['shortForecast']}"
            )
            say(weather_message)
        else:
            say("Sorry, I couldn't fetch the weather data at the moment.")
    elif intent_data.get("intent") == "chat":
        # For chat intent, use the regular ask_chatgpt function
        chatgpt_response = ask_chatgpt(user_message)
        say(chatgpt_response)
    else:
        say("Sorry, I couldn't understand your request.")

# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 8000)))
