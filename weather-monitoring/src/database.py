from flask_sqlalchemy import SQLAlchemy
from models import db, WeatherData

def init_db(app):
    """Initialize database"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()

def save_weather_data(data):
    """Save weather data to database"""
    weather = WeatherData(
        city=data['city'],
        country=data.get('country'),
        temperature=data['temperature'],
        humidity=data.get('humidity'),
        pressure=data.get('pressure'),
        description=data.get('description'),
        wind_speed=data.get('wind_speed')
    )
    
    db.session.add(weather)
    db.session.commit()
    return weather

def get_all_weather_data():
    """Get all weather data"""
    return WeatherData.query.order_by(WeatherData.created_at.desc()).all()

def get_weather_by_city(city):
    """Get weather data by city"""
    return WeatherData.query.filter_by(city=city.lower()).order_by(WeatherData.created_at.desc()).all()
