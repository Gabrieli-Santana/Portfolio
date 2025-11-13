"""
🌦️ Weather Monitoring System
Sistema completo de monitoramento climático
"""

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

class Config:
    # Database - usando SQLite para simplicidade
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///weather.db')
    
    # OpenWeather API - SUA CHAVE JÁ ESTÁ AQUI
    OPENWEATHER_API_KEY = '05f77f0d164c53af43212ce6c239de77'
    OPENWEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
    
    # App
    DEBUG = True

# =============================================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# =============================================================================

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =============================================================================
# MODELOS DO BANCO DE DADOS
# =============================================================================

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

# =============================================================================
# FUNÇÕES DE API EXTERNA - TUDO DENTRO DO MESMO ARQUIVO
# =============================================================================

def get_weather_data(city_name):
    """
    Busca dados climáticos da OpenWeather API
    """
    print(f"🌐 Buscando dados climáticos para: {city_name}")
    
    params = {
        'q': city_name,
        'appid': Config.OPENWEATHER_API_KEY,
        'units': 'metric',
        'lang': 'pt_br'
    }
    
    try:
        response = requests.get(Config.OPENWEATHER_BASE_URL, params=params, timeout=10)
        
        if response.status_code == 401:
            return {'error': 'API key inválida ou expirada'}
        elif response.status_code == 404:
            return {'error': 'Cidade não encontrada'}
        elif response.status_code != 200:
            return {'error': f'Erro na API: {response.status_code}'}
        
        response.raise_for_status()
        data = response.json()
        
        # Extrair dados relevantes
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

# =============================================================================
# FUNÇÕES DE BANCO DE DADOS - TUDO DENTRO DO MESMO ARQUIVO
# =============================================================================

def save_weather_data(data):
    """Salva dados climáticos no banco de dados"""
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
        print(f"💾 Dados salvos no banco: {weather.city}")
        return weather
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao salvar no banco: {e}")
        return None

def get_all_weather_data():
    """Busca todos os dados climáticos do banco"""
    try:
        return WeatherData.query.order_by(WeatherData.created_at.desc()).all()
    except Exception as e:
        print(f"❌ Erro ao buscar dados: {e}")
        return []

def get_weather_by_city(city):
    """Busca dados climáticos por cidade"""
    try:
        return WeatherData.query.filter(WeatherData.city.ilike(f"%{city}%")).order_by(WeatherData.created_at.desc()).all()
    except Exception as e:
        print(f"❌ Erro ao buscar dados da cidade: {e}")
        return []

# =============================================================================
# ENDPOINTS DA API - SIMPLES E FUNCIONAIS
# =============================================================================

@app.route('/')
def home():
    """Página inicial com documentação"""
    return {
        'message': '🌦️ Weather Monitoring API - PORTOFÓLIO ADS',
        'estudante': 'Seu Nome - 2º Semestre ADS',
        'version': '1.0.0',
        'endpoints': {
            'GET /': 'Documentação da API',
            'GET /health': 'Health check do sistema',
            'GET /api/weather': 'Listar todos os dados climáticos',
            'POST /api/weather': 'Buscar e salvar dados de uma cidade',
            'GET /api/weather/<city>': 'Buscar dados por cidade',
            'GET /api/stats': 'Estatísticas do sistema'
        },
        'exemplo_uso': 'curl -X POST http://localhost:5000/api/weather -H "Content-Type: application/json" -d \'{"city": "São Paulo"}\''
    }

@app.route('/health')
def health():
    """Health check - verifica se a API está funcionando"""
    try:
        # Testa conexão com banco
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'erro: {str(e)}'
    
    return {
        'status': 'online',
        'database': db_status,
        'timestamp': datetime.utcnow().isoformat(),
        'message': '✅ API funcionando corretamente'
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
        # Verifica se recebeu JSON
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
        
        print(f"📍 Recebida solicitação para cidade: {city}")
        
        # Busca dados da API externa
        weather_info = get_weather_data(city)
        
        if 'error' in weather_info:
            return {
                'status': 'error',
                'message': weather_info['error']
            }, 400
        
        # Salva no banco de dados
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

@app.route('/api/weather/<string:city>', methods=['GET'])
def get_city_weather(city):
    """Busca dados climáticos de uma cidade específica"""
    try:
        weather_data = get_weather_by_city(city)
        
        return {
            'status': 'success',
            'city': city,
            'data': [data.to_dict() for data in weather_data],
            'count': len(weather_data),
            'timestamp': datetime.utcnow().isoformat()
        }, 200
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Erro ao buscar dados para {city}: {str(e)}'
        }, 500

@app.route('/api/stats', methods=['GET'])
def get_system_stats():
    """Retorna estatísticas do sistema"""
    try:
        total_records = WeatherData.query.count()
        
        # Conta cidades distintas
        cities = db.session.query(WeatherData.city).distinct().all()
        cities_count = len(cities)
        
        # Último registro
        latest = WeatherData.query.order_by(WeatherData.created_at.desc()).first()
        
        return {
            'status': 'success',
            'estatisticas': {
                'total_registros': total_records,
                'cidades_monitoradas': cities_count,
                'lista_cidades': [city[0] for city in cities],
                'ultimo_registro': latest.to_dict() if latest else None
            },
            'timestamp': datetime.utcnow().isoformat()
        }, 200
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Erro ao buscar estatísticas: {str(e)}'
        }, 500

# =============================================================================
# INICIALIZAÇÃO SIMPLIFICADA
# =============================================================================

def init_database():
    """Inicializa o banco de dados - VERSÃO SIMPLIFICADA"""
    with app.app_context():
        db.create_all()
        print("✅ Banco de dados inicializado com sucesso!")

# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

if __name__ == '__main__':
    print("🌦️  INICIANDO WEATHER MONITORING SYSTEM")
    print("=" * 60)
    print("ESTUDANTE: Seu Nome - 2º Semestre ADS")
    print("FUNCIONALIDADES:")
    print("  ✅ API RESTful com Flask")
    print("  ✅ Banco de dados SQLite")
    print("  ✅ Integração com OpenWeather API")
    print("  ✅ CRUD completo de dados climáticos")
    print("=" * 60)
    
    # Inicializa banco de dados
    init_database()
    
    print("\n🚀 SERVIDOR INICIANDO...")
    print("📍 ENDPOINTS DISPONÍVEIS:")
    print("   http://localhost:5000/          - Documentação")
    print("   http://localhost:5000/health    - Health Check")
    print("   http://localhost:5000/api/weather - API Principal")
    print("=" * 60)
    print("💡 DICA: Teste no navegador ou use os comandos curl abaixo")
    print("📝 EXEMPLOS:")
    print('   curl -X POST http://localhost:5000/api/weather \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"city": "São Paulo"}\'')
    print('   curl http://localhost:5000/api/weather')
    print("=" * 60)
    
    # Executa a aplicação
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)