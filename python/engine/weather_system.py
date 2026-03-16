import requests

class Wheather_Engine:
    def __init__(self):
        # -> OpenWeather se tempreature pta lagayenge
        self.api_key = "7c880ab8a64eddb3de89b7e500536d9c"
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

    def get_weather(self, city):
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric', # -> Tempreature celsius mein aayega isse
            'lang': 'en'       # -> Language english
        }
        
        print(f"\n🔍 Fetching weather data for: {city}...")
        
        try:
            response = requests.get(self.base_url, params=params) # -> Servers se data le rhe hain,Json format mein
            data = response.json()

            if data["cod"] == 200:
                # -> Data lenge aur display karenge
                temp = data['main']['temp']
                desc = data['weather'][0]['description']
                
                # -> (Precipitation, Wind, Humidity)
                humidity = data['main']['humidity']
                wind_speed = data['wind']['speed']
                
                # -> Rain ka data optional hai..
                rain = data.get('rain', {}).get('1h', 0) 

                print("-" * 30)
                print(f"✅ Success! Weather in {city.capitalize()}:")
                print(f"🌡️  Temperature: {temp}°C")
                print(f"☁️  Condition: {desc.title()}")
                print(f"💧  Humidity: {humidity}%")
                print(f"💨  Wind Speed: {wind_speed} m/s")
                
                if rain > 0:
                    print(f"🌧️  Precipitation (last 1h): {rain} mm")
                else:
                    print(f"☀️  Precipitation: No rain reported.")
                print("-" * 30)
                
                # **ADD THIS RETURN STATEMENT:**
                return f"Temperature: {temp}°C, Condition: {desc.title()}, Humidity: {humidity}%, Wind: {wind_speed} m/s"
                
            else:
                print(f"❌ Error: {data['message']}")
                return f"Weather data not available for {city}. Error: {data['message']}"
                
        except Exception as e:
            print(f"❌ Something went wrong: {e}")
            return f"Failed to get weather data for {city}. Error: {e}"

# -> User se input leke weather check karenge
if __name__ == "__main__":
    bot = Wheather_Engine()  # Fixed class name here too
    city = input("Enter City Name: ")
    result = bot.get_weather(city)
    print(f"Returned: {result}")