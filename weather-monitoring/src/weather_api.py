import requests
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, List

# Configurar logging
logger = logging.getLogger(__name__)

class WeatherAPI:
    """Classe para interagir com a API do OpenWeatherMap"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
        if not self.api_key:
            logger.warning("OpenWeather API key não encontrada")
    
    def get_current_weather(self, city: str, country_code: str = None) -> Optional[Dict]:
        """
        Obter dados meteorológicos atuais para uma cidade
        
        Args:
            city: Nome da cidade
            country_code: Código do país (opcional)
        
        Returns:
            Dict com dados meteorológicos ou None em caso de erro
        """
        try:
            # Construir query
            query = city
            if country_code:
                query += f",{country_code}"
            
            # Fazer requisição
            url = f"{self.base_url}/weather"
            params = {
                'q': query,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'pt_br'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Processar e formatar dados
            processed_data = {
                'city': data['name'],
                'country': data['sys']['country'],
                'temperature': round(data['main']['temp'], 1),
                'feels_like': round(data['main']['feels_like'], 1),
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description'].title(),
                'icon': data['weather'][0]['icon'],
                'wind_speed': data['wind']['speed'],
                'wind_deg': data.get('wind', {}).get('deg', 0),
                'visibility': data.get('visibility', 0),
                'clouds': data['clouds']['all'],
                'sunrise': datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M'),
                'sunset': datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M'),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Dados meteorológicos obtidos para {city}")
            return processed_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {city}: {e}")
            return None
        except KeyError as e:
            logger.error(f"Dados incompletos da API para {city}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado para {city}: {e}")
            return None
    
    def get_weather_forecast(self, city: str, country_code: str = None, days: int = 5) -> Optional[List[Dict]]:
        """
        Obter previsão do tempo para os próximos dias
        
        Args:
            city: Nome da cidade
            country_code: Código do país (opcional)
            days: Número de dias da previsão (máx. 5)
        
        Returns:
            Lista de dicionários com previsão ou None em caso de erro
        """
        try:
            # Construir query
            query = city
            if country_code:
                query += f",{country_code}"
            
            # Fazer requisição
            url = f"{self.base_url}/forecast"
            params = {
                'q': query,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'pt_br',
                'cnt': days * 8  # 8 previsões por dia (3 horas cada)
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Processar previsões
            forecasts = []
            current_date = None
            daily_forecast = None
            
            for forecast in data['list']:
                forecast_date = datetime.fromtimestamp(forecast['dt']).date()
                
                # Nova previsão diária
                if forecast_date != current_date:
                    if daily_forecast:
                        forecasts.append(daily_forecast)
                    
                    current_date = forecast_date
                    daily_forecast = {
                        'date': forecast_date.strftime('%Y-%m-%d'),
                        'day_name': forecast_date.strftime('%A'),
                        'temp_min': forecast['main']['temp_min'],
                        'temp_max': forecast['main']['temp_max'],
                        'description': forecast['weather'][0]['description'].title(),
                        'icon': forecast['weather'][0]['icon'],
                        'humidity': forecast['main']['humidity'],
                        'wind_speed': forecast['wind']['speed'],
                        'precipitation': forecast.get('pop', 0) * 100  # Probabilidade de chuva em %
                    }
                else:
                    # Atualizar mínimas e máximas
                    daily_forecast['temp_min'] = min(daily_forecast['temp_min'], forecast['main']['temp_min'])
                    daily_forecast['temp_max'] = max(daily_forecast['temp_max'], forecast['main']['temp_max'])
            
            # Adicionar última previsão
            if daily_forecast:
                forecasts.append(daily_forecast)
            
            logger.info(f"Previsão obtida para {city} - {len(forecasts)} dias")
            return forecasts[:days]  # Limitar ao número solicitado de dias
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição de previsão para {city}: {e}")
            return None
        except KeyError as e:
            logger.error(f"Dados incompletos da previsão para {city}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado na previsão para {city}: {e}")
            return None
    
    def get_weather_by_coordinates(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Obter dados meteorológicos por coordenadas
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Dict com dados meteorológicos ou None em caso de erro
        """
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'pt_br'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            processed_data = {
                'city': data['name'],
                'country': data['sys']['country'],
                'temperature': round(data['main']['temp'], 1),
                'feels_like': round(data['main']['feels_like'], 1),
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description'].title(),
                'icon': data['weather'][0]['icon'],
                'wind_speed': data['wind']['speed'],
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Dados obtidos por coordenadas: {lat}, {lon}")
            return processed_data
            
        except Exception as e:
            logger.error(f"Erro ao obter dados por coordenadas {lat}, {lon}: {e}")
            return None
    
    def validate_api_key(self) -> bool:
        """
        Validar se a API key está funcionando
        
        Returns:
            bool: True se a key é válida, False caso contrário
        """
        try:
            url = f"{self.base_url}/weather"
            params = {
                'q': 'London',
                'appid': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            return response.status_code == 200
            
        except Exception:
            return False


# Função de utilidade para criar instância da API
def create_weather_api() -> WeatherAPI:
    """Factory function para criar instância do WeatherAPI"""
    return WeatherAPI()


# Exemplo de uso
if __name__ == "__main__":
    # Configurar logging básico
    logging.basicConfig(level=logging.INFO)
    
    # Testar a API (substitua pela sua chave real)
    api = WeatherAPI(api_key="sua_chave_aqui")
    
    if api.validate_api_key():
        print("✅ API Key válida")
        
        # Testar dados atuais
        current_weather = api.get_current_weather("São Paulo", "BR")
        if current_weather:
            print(f"🌤️  Clima em {current_weather['city']}:")
            print(f"   Temperatura: {current_weather['temperature']}°C")
            print(f"   Descrição: {current_weather['description']}")
        
        # Testar previsão
        forecast = api.get_weather_forecast("Rio de Janeiro", "BR", 3)
        if forecast:
            print(f"\n📅 Previsão para {len(forecast)} dias:")
            for day in forecast:
                print(f"   {day['day_name']}: {day['temp_min']}°C - {day['temp_max']}°C, {day['description']}")
    else:
        print("❌ API Key inválida ou não configurada")
        print("💡 Configure a variável de ambiente OPENWEATHER_API_KEY")