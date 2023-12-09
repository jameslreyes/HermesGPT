import requests
import Levenshtein
import googlemaps
from classes.calculations import DateTime
from config import Config

def get_current_weather():
    gmaps = googlemaps.Client(key=Config.GOOGLE_API_KEY)

    # Load known cities from a file
    with open("D:/!AI & ML/!Apps/Python - TelegramGPT/scripts/cities.txt", "r") as f:
        known_cities = [line.strip() for line in f.readlines()]

    def closest_city(input_city):
        distances = [(Levenshtein.distance(input_city.lower(), known.lower()), known) for known in known_cities]
        closest = min(distances, key=lambda x: x[0])
        return closest[1]

    def get_state_from_coordinates(lat, lon):
        try:
            reverse_geocode_result = gmaps.reverse_geocode((lat, lon))
            for component in reverse_geocode_result[0]['address_components']:
                if 'administrative_area_level_1' in component['types']:
                    state = component['short_name']
                    return state
            return "Unknown"
        except Exception as e:
            print("Unable to fetch state data")
            print(f"Exception: {e}")
            return "Unknown"

    while True:
        city = input("Enter the name of the city: ")
        closest_city(city)
        break

    try:
        api_key = Config.WEATHER_API_KEY
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric"
        }

        response = requests.get(base_url, params=params)
        data = response.json()
        
        if response.status_code == 200:
            weather = data["weather"][0]["description"]
            temperature = round(data["main"]["temp"] * 9/5 + 32)
            
            lat = data["coord"]["lat"]
            lon = data["coord"]["lon"]
            
            state = get_state_from_coordinates(lat, lon)
            city = city.title()
            
            return f"The current weather in {city}, {state} is {weather} with a temperature of {temperature}°F."
        else:
            return "Failed to fetch weather data."
    except Exception as e:
        return f"Unable to fetch weather data: {e}"

def main():
    print("Select an option:")
    print("1: Get current weather")
    print("2: Get current date")
    print("3: Get current time")
    
    choice = input("Enter your choice: ")
    
    if choice == '1':
        print(get_current_weather())
    elif choice == '2':
        print("Current date:", DateTime.get_current_date())
    elif choice == '3':
        print("Current time:", DateTime.get_current_time())
    else:
        print("Invalid choice, exiting.")

if __name__ == "__main__":
    main()