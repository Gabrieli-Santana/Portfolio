import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///weather.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo para histórico de consultas
class WeatherQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(2), nullable=False)
    temperature = db.Column(db.Float)
    description = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Simulação da API de Clima
class WeatherAPI:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY', '05f77f0d164c53af43212ce6c239de77')
    
    def get_current_weather(self, city, country_code=None):
        """Simulação - em produção, isso faria requisição real à API"""
        # Dados de exemplo para demonstração
        import random
        return {
            'city': city,
            'country': country_code or 'BR',
            'temperature': round(random.uniform(15, 35), 1),
            'feels_like': round(random.uniform(14, 34), 1),
            'humidity': random.randint(30, 90),
            'pressure': random.randint(1000, 1020),
            'description': ['Ensolarado', 'Nublado', 'Chuvoso', 'Parcialmente nublado'][random.randint(0, 3)],
            'icon': '01d',
            'wind_speed': round(random.uniform(0, 15), 1),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_weather_forecast(self, city, country_code=None, days=5):
        """Simulação de previsão"""
        import random
        forecasts = []
        for i in range(days):
            forecasts.append({
                'date': (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d'),
                'day_name': (datetime.now() + timedelta(days=i)).strftime('%A'),
                'temp_min': round(random.uniform(15, 20), 1),
                'temp_max': round(random.uniform(25, 35), 1),
                'description': ['Ensolarado', 'Nublado', 'Chuvoso'][random.randint(0, 2)],
                'icon': '01d',
                'humidity': random.randint(40, 80),
                'wind_speed': round(random.uniform(0, 12), 1)
            })
        return forecasts

weather_api = WeatherAPI()

# Criar tabelas antes do primeiro request
with app.app_context():
    db.create_all()
    logger.info("✅ Tabelas do banco de dados criadas")

@app.route('/')
def index():
    """Página inicial com monitoramento climático"""
    return render_template('index.html')

@app.route('/api/weather/current')
def get_current_weather():
    """API para obter clima atual"""
    city = request.args.get('city', 'São Paulo')
    country = request.args.get('country', 'BR')
    
    try:
        weather_data = weather_api.get_current_weather(city, country)
        
        # Salvar no banco
        query = WeatherQuery(
            city=city,
            country=country,
            temperature=weather_data['temperature'],
            description=weather_data['description']
        )
        db.session.add(query)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': weather_data
        })
    except Exception as e:
        logger.error(f"Erro ao obter clima: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@app.route('/api/weather/forecast')
def get_weather_forecast():
    """API para obter previsão do tempo"""
    city = request.args.get('city', 'São Paulo')
    country = request.args.get('country', 'BR')
    days = int(request.args.get('days', 5))
    
    try:
        forecast_data = weather_api.get_weather_forecast(city, country, days)
        return jsonify({
            'success': True,
            'data': forecast_data
        })
    except Exception as e:
        logger.error(f"Erro na previsão: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter previsão'
        }), 500

@app.route('/api/history')
def get_query_history():
    """Histórico de consultas"""
    queries = WeatherQuery.query.order_by(WeatherQuery.timestamp.desc()).limit(10).all()
    history = [{
        'city': q.city,
        'country': q.country,
        'temperature': q.temperature,
        'description': q.description,
        'timestamp': q.timestamp.isoformat()
    } for q in queries]
    
    return jsonify({
        'success': True,
        'data': history
    })

@app.route('/api/health')
def health_check():
    """Endpoint de saúde da aplicação"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Weather Monitoring API',
        'database': 'SQLite'
    })

@app.route('/dashboard')
def dashboard():
    """Dashboard de monitoramento climático"""
    return render_template('dashboard.html')

if __name__ == '__main__':
    # Criar diretório para banco de dados
    os.makedirs('instance', exist_ok=True)
    
    logger.info("🚀 Iniciando servidor Weather Monitoring...")
    logger.info("📊 Acesse: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)