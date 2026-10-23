import requests
import random
import math
from datetime import datetime, timedelta
from flask import current_app


def get_weather_data(city: str) -> dict:
    api_key = current_app.config.get('WEATHER_API_KEY', '')
    base_url = current_app.config.get('WEATHER_API_BASE', '')

    if api_key and api_key != 'demo-key':
        try:
            url = f"{base_url}/weather?q={city}&appid={api_key}&units=metric"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'city': data['name'],
                    'temperature': round(data['main']['temp'], 1),
                    'feels_like': round(data['main']['feels_like'], 1),
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'wind_speed': round(data['wind']['speed'] * 3.6, 1),
                    'description': data['weather'][0]['description'].title(),
                    'icon': data['weather'][0]['icon'],
                    'visibility': data.get('visibility', 10000) / 1000,
                    'source': 'live'
                }
        except Exception:
            pass

    return _generate_mock_weather(city)


def get_forecast_data(city: str) -> list:
    api_key = current_app.config.get('WEATHER_API_KEY', '')
    base_url = current_app.config.get('WEATHER_API_BASE', '')

    if api_key and api_key != 'demo-key':
        try:
            url = f"{base_url}/forecast?q={city}&appid={api_key}&units=metric&cnt=40"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                forecast = []
                for item in data['list']:
                    forecast.append({
                        'datetime': item['dt_txt'],
                        'temperature': round(item['main']['temp'], 1),
                        'humidity': item['main']['humidity'],
                        'pressure': item['main']['pressure'],
                        'wind_speed': round(item['wind']['speed'] * 3.6, 1),
                        'description': item['weather'][0]['description'].title(),
                        'icon': item['weather'][0]['icon']
                    })
                return forecast
        except Exception:
            pass

    return _generate_mock_forecast(city)


def _generate_mock_weather(city: str) -> dict:
    seed = sum(ord(c) for c in city)
    random.seed(seed + int(datetime.now().hour))

    temp = round(random.uniform(5, 38), 1)
    conditions = ['Clear Sky', 'Partly Cloudy', 'Overcast', 'Light Rain', 'Thunderstorm', 'Fog', 'Snow']
    icons = ['01d', '02d', '03d', '10d', '11d', '50d', '13d']
    idx = random.randint(0, len(conditions) - 1)

    return {
        'city': city,
        'temperature': temp,
        'feels_like': round(temp - random.uniform(1, 5), 1),
        'humidity': random.randint(30, 95),
        'pressure': random.randint(990, 1030),
        'wind_speed': round(random.uniform(5, 80), 1),
        'description': conditions[idx],
        'icon': icons[idx],
        'visibility': round(random.uniform(1, 20), 1),
        'source': 'simulated'
    }


def _generate_mock_forecast(city: str) -> list:
    forecast = []
    base_temp = random.uniform(10, 30)
    now = datetime.now()

    for i in range(40):
        dt = now + timedelta(hours=i * 3)
        hour_factor = math.sin(math.pi * dt.hour / 12)
        temp = round(base_temp + hour_factor * 5 + random.uniform(-2, 2), 1)
        conditions = ['Clear Sky', 'Partly Cloudy', 'Overcast', 'Light Rain']
        icons = ['01d', '02d', '03d', '10d']
        idx = random.randint(0, 3)

        forecast.append({
            'datetime': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': temp,
            'humidity': random.randint(35, 90),
            'pressure': random.randint(995, 1025),
            'wind_speed': round(random.uniform(5, 60), 1),
            'description': conditions[idx],
            'icon': icons[idx]
        })

    return forecast
