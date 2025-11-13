from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class WeatherData(db.Model):
    __tablename__ = 'weather_data'
    
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(10))
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Integer)
    pressure = db.Column(db.Integer)
    description = db.Column(db.String(200))
    wind_speed = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'country': self.country,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'description': self.description,
            'wind_speed': self.wind_speed,
            'created_at': self.created_at.isoformat()
        }
