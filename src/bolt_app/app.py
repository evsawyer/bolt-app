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

# Initialize the Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Function to get weather data from api.weather.gov
def get_weather():
    latitude = "32.7481"
    longitude = "-117.1313"
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

# Listens for app_mention events
@app.event("app_mention")
def handle_app_mention_events(body, say):
    event = body.get("event", {})
    text = event.get("text", "").lower()
    
    if "weather" in text:
        weather_data = get_weather()
        if weather_data:
            weather_message = (
                f"Current weather in University Heights, San Diego:\n"
                f"Temperature: {weather_data['temperature']}°{weather_data['temperatureUnit']}\n"
                f"Wind: {weather_data['windSpeed']} from {weather_data['windDirection']}\n"
                f"Forecast: {weather_data['shortForecast']}"
            )
            say(weather_message)
        else:
            say("Sorry, I couldn't fetch the weather data at the moment.")
    else:
        question = text.replace("@dummybot", "").strip()
        print(question)
        chatgpt_response = ask_chatgpt(question)
        say(chatgpt_response)

# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 8000)))
