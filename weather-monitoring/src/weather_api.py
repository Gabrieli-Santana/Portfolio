# 🌦️ Weather Monitoring System 

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
            'temperature': round(self.temperature, 2),
            'humidity': self.humidity,
            'pressure': self.pressure,
            'description': self.description,
            'wind_speed': round(self.wind_speed, 2),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


def get_weather_data(city_name):
    """
    Busca dados climáticos da OpenWeather API
    """
    print(f"🌐 Buscando dados para: {city_name}")
    
    API_KEY = '05f77f0d164c53af43212ce6c239de77'
    
    params = {
        'q': city_name,
        'appid': API_KEY,
        'units': 'metric',
        'lang': 'pt_br'
    }
    
    try:
        response = requests.get("http://api.openweathermap.org/data/2.5/weather", 
                              params=params, timeout=10)
        
        if response.status_code == 401:
            return {'error': 'API key inválida ou expirada'}
        elif response.status_code == 404:
            return {'error': 'Cidade não encontrada'}
        elif response.status_code != 200:
            return {'error': f'Erro na API: {response.status_code}'}
        
        data = response.json()
        
        weather_info = {
            'city': data['name'],
            'country': data['sys']['country'],
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'description': data['weather'][0]['description'],
            'wind_speed': data['wind']['speed']
        }
        
        print(f"✅ Dados obtidos: {weather_info['temperature']}°C em {weather_info['city']}")
        return weather_info
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        return {'error': f'Falha ao buscar dados: {str(e)}'}
    except KeyError as e:
        print(f"❌ Erro ao processar dados: {e}")
        return {'error': f'Dados inválidos da API: {str(e)}'}

def save_weather_data(data):
    """Salva dados climáticos no banco"""
    if 'error' in data:
        return None
        
    weather = WeatherData(
        city=data['city'],
        country=data.get('country'),
        temperature=data['temperature'],
        humidity=data.get('humidity'),
        pressure=data.get('pressure'),
        description=data.get('description'),
        wind_speed=data.get('wind_speed')
    )
    
    try:
        db.session.add(weather)
        db.session.commit()
        print(f"💾 Dados salvos: {weather.city}")
        return weather
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao salvar: {e}")
        return None

def get_all_weather_data():
    """Busca todos os dados do banco"""
    try:
        return WeatherData.query.order_by(WeatherData.created_at.desc()).all()
    except Exception as e:
        print(f"❌ Erro ao buscar dados: {e}")
        return []


@app.route('/')
def home():
    """Página inicial com documentação"""
    return {
        'message': '🌦️ Weather Monitoring API - Portfolio ADS',
        'estudante': 'Ana Carolina - 2º Semestre ADS',
        'version': '1.0.0',
        'endpoints': {
            'GET /': 'Documentação da API',
            'GET /health': 'Health check do sistema',
            'GET /api/weather': 'Listar todos os dados climáticos',
            'POST /api/weather': 'Buscar e salvar dados de uma cidade'
        },
        'exemplo_uso': 'Use: curl -X POST http://localhost:5000/api/weather -H "Content-Type: application/json" -d \'{"city": "São Paulo"}\''
    }

@app.route('/health')
def health():
    """Health check - verifica se está funcionando"""
    try:
  
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'erro: {str(e)}'
    
    return {
        'status': 'online',
        'database': db_status,
        'timestamp': datetime.utcnow().isoformat()
    }

@app.route('/api/weather', methods=['GET'])
def get_all_weather():
    """Busca todos os dados climáticos armazenados"""
    try:
        weather_data = get_all_weather_data()
        return {
            'status': 'success',
            'data': [data.to_dict() for data in weather_data],
            'count': len(weather_data),
            'timestamp': datetime.utcnow().isoformat()
        }, 200
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Erro ao buscar dados: {str(e)}'
        }, 500

@app.route('/api/weather', methods=['POST'])
def create_weather():
    """Busca dados da OpenWeather e salva no banco"""
    try:
        if not request.is_json:
            return {
                'status': 'error',
                'message': 'Content-Type deve ser application/json'
            }, 400
        
        data = request.get_json()
        city = data.get('city')
        
        if not city:
            return {
                'status': 'error',
                'message': 'Parâmetro "city" é obrigatório'
            }, 400
        
        print(f"📍 Buscando dados para: {city}")
        
        weather_info = get_weather_data(city)
        
        if 'error' in weather_info:
            return {
                'status': 'error',
                'message': weather_info['error']
            }, 400
        
        saved_data = save_weather_data(weather_info)
        
        if not saved_data:
            return {
                'status': 'error',
                'message': 'Erro ao salvar dados no banco'
            }, 500
        
        return {
            'status': 'success',
            'message': f'Dados climáticos de {city} salvos com sucesso!',
            'data': saved_data.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        }, 201
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Erro interno: {str(e)}'
        }, 500


def init_database():
    """Inicializa o banco de dados"""
    with app.app_context():
        db.create_all()
        print("✅ Banco de dados inicializado com sucesso!")

if __name__ == '__main__':
    print("🌦️  WEATHER MONITORING SYSTEM - PORTFOLIO ADS")
    print("=" * 50)
    print("Desenvolvido por: Ana Carolina")
    print("Curso: Análise e Desenvolvimento de Sistemas - 2º Semestre")
    print("=" * 50)
    
    init_database()
    
    print("\n🚀 SERVIDOR INICIANDO...")
    print("📍 ACESSE: http://localhost:5000")
    print("💡 TESTE: http://localhost:5000/health")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
