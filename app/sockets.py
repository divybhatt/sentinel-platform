from flask_socketio import emit, join_room, leave_room
from flask import request
import threading
import time


def register_events(socketio):

    @socketio.on('connect')
    def on_connect():
        emit('connected', {'status': 'Connected to Sentinel live feed'})

    @socketio.on('subscribe_weather')
    def on_subscribe(data):
        city = data.get('city', 'New York')
        join_room(f'weather_{city}')
        emit('subscribed', {'city': city, 'message': f'Subscribed to {city} live updates'})
        # Start a background push immediately
        _push_weather_update(socketio, city)

    @socketio.on('unsubscribe_weather')
    def on_unsubscribe(data):
        city = data.get('city', '')
        leave_room(f'weather_{city}')

    @socketio.on('disconnect')
    def on_disconnect():
        pass

    # Background thread: push updates every 30 seconds
    def background_push():
        default_cities = ['New York', 'London', 'Tokyo', 'Mumbai', 'Sydney']
        while True:
            time.sleep(30)
            for city in default_cities:
                try:
                    _push_weather_update(socketio, city)
                except Exception:
                    pass

    t = threading.Thread(target=background_push, daemon=True)
    t.start()


def _push_weather_update(socketio, city):
    try:
        from app.weather.services import get_weather_data
        from app.ml.risk_engine import predict_risk
        w = get_weather_data(city)
        r = predict_risk(w['temperature'], w['humidity'], w['wind_speed'], w['pressure'])
        payload = {
            'city': city,
            'temperature': w['temperature'],
            'humidity': w['humidity'],
            'wind_speed': w['wind_speed'],
            'pressure': w['pressure'],
            'description': w['description'],
            'risk_score': r['score'],
            'risk_level': r['level'],
            'risk_color': r['color'],
            'timestamp': time.strftime('%H:%M:%S')
        }
        socketio.emit('weather_update', payload, room=f'weather_{city}')
    except Exception as e:
        pass