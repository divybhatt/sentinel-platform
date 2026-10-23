from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, current_user
from app.weather.services import get_weather_data, get_forecast_data
from app.ml.risk_engine import predict_risk
import html

weather_bp = Blueprint('weather', __name__)


@weather_bp.route('/current')
@jwt_required()
def current_weather():
    city = request.args.get('city', current_user.city)
    city = html.escape(city.strip())

    weather = get_weather_data(city)
    risk_data = predict_risk(
        temperature=weather['temperature'],
        humidity=weather['humidity'],
        wind_speed=weather['wind_speed'],
        pressure=weather['pressure']
    )

    # Pass app explicitly to avoid context issues in thread
    try:
        from app.alerts import check_and_alert
        app = current_app._get_current_object()
        alert_sent = check_and_alert(current_user, weather, risk_data, app)
        risk_data['alert_sent'] = alert_sent
    except Exception as e:
        print(f"Alert check error: {e}")
        risk_data['alert_sent'] = False

    return jsonify({'weather': weather, 'risk': risk_data})


@weather_bp.route('/forecast')
@jwt_required()
def forecast():
    city = request.args.get('city', current_user.city)
    city = html.escape(city.strip())

    forecast_data = get_forecast_data(city)
    enriched = []
    for item in forecast_data:
        risk = predict_risk(
            temperature=item['temperature'],
            humidity=item['humidity'],
            wind_speed=item['wind_speed'],
            pressure=item['pressure']
        )
        item['risk_score'] = risk['score']
        item['risk_level'] = risk['level']
        enriched.append(item)

    return jsonify({'forecast': enriched, 'city': city})


@weather_bp.route('/risk-history')
@jwt_required()
def risk_history():
    from app.weather.services import _generate_mock_forecast
    city = request.args.get('city', current_user.city)

    forecast_data = _generate_mock_forecast(city)
    history = []
    for item in forecast_data[:20]:
        risk = predict_risk(
            temperature=item['temperature'],
            humidity=item['humidity'],
            wind_speed=item['wind_speed'],
            pressure=item['pressure']
        )
        history.append({
            'datetime': item['datetime'],
            'risk_score': risk['score'],
            'risk_level': risk['level'],
            'temperature': item['temperature'],
            'humidity': item['humidity'],
            'wind_speed': item['wind_speed']
        })

    return jsonify({'history': history, 'city': city})


@weather_bp.route('/compare')
@jwt_required()
def compare_cities():
    city1 = html.escape(request.args.get('city1', 'New York').strip())
    city2 = html.escape(request.args.get('city2', 'London').strip())

    def get_city_data(city):
        w = get_weather_data(city)
        r = predict_risk(w['temperature'], w['humidity'], w['wind_speed'], w['pressure'])
        return {'weather': w, 'risk': r}

    return jsonify({
        'city1': get_city_data(city1),
        'city2': get_city_data(city2)
    })