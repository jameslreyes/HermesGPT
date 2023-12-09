import requests
from config import Config

class WeatherHandler():
    def __init__(self):
        pass

    def get_current_weather(location):
        """
        Get the current weather for a given location.

        Args:
            location (str): The location for which to retrieve the weather.

        Returns:
            dict: A dictionary containing the weather description and temperature.

        Example:
            >>> get_current_weather("London")
            {'description': 'clear sky', 'temperature': 17.0}
        """
        api_key = Config.WEATHER_API_KEY
        base_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}"
        response = requests.get(base_url)
        data = response.json()
        if data.get("message"):
            return {"error": data['message']}
        else:
            description = data["weather"][0]["description"]
            temp = round(data["main"]["temp"] - 273.15, 2) # Convert Kelvin to Celsius
            return {"description": description, "temperature": temp}