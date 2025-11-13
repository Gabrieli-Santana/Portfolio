import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://weather_user:weather_pass@localhost:5432/weather_db')
    
    # OpenWeather API
    OPENWEATHER_API_KEY = os.getenv('05f77f0d164c53af43212ce6c239de77')
    OPENWEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
    
    # App
    DEBUG = os.getenv('DEBUG', False)