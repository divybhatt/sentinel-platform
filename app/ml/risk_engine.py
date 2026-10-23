import joblib
import numpy as np
import os
from threading import Lock

_model = None
_model_lock = Lock()
_model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml', 'model.joblib')


def _get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                if os.path.exists(_model_path):
                    _model = joblib.load(_model_path)
                else:
                    _model = _FallbackModel()
    return _model


class _FallbackModel:
    def predict(self, X):
        temp, hum, wind, pressure = X[0]
        score = (
            max(0, (temp - 20) / 30 * 25) +
            max(0, (hum - 50) / 50 * 20) +
            max(0, wind / 150 * 35) +
            max(0, (1013 - pressure) / 63 * 20)
        )
        return [np.clip(score, 0, 100)]


def predict_risk(temperature: float, humidity: float, wind_speed: float, pressure: float) -> dict:
    model = _get_model()
    features = np.array([[temperature, humidity, wind_speed, pressure]])
    score = float(np.clip(model.predict(features)[0], 0, 100))

    if score < 25:
        level = 'LOW'
        color = '#10b981'
        description = 'Conditions are safe. No significant weather threats detected.'
    elif score < 50:
        level = 'MODERATE'
        color = '#f59e0b'
        description = 'Moderate risk. Monitor conditions for changes.'
    elif score < 75:
        level = 'HIGH'
        color = '#f97316'
        description = 'High risk. Take precautionary measures.'
    else:
        level = 'CRITICAL'
        color = '#ef4444'
        description = 'Critical conditions. Immediate action may be required.'

    return {
        'score': round(score, 1),
        'level': level,
        'color': color,
        'description': description,
        'factors': _get_risk_factors(temperature, humidity, wind_speed, pressure)
    }


def _get_risk_factors(temp, humidity, wind, pressure) -> list:
    factors = []
    if wind > 60:
        factors.append({'name': 'High Winds', 'severity': 'high', 'value': f'{wind:.1f} km/h'})
    elif wind > 30:
        factors.append({'name': 'Moderate Winds', 'severity': 'medium', 'value': f'{wind:.1f} km/h'})

    if temp > 38 or temp < -10:
        factors.append({'name': 'Extreme Temperature', 'severity': 'high', 'value': f'{temp:.1f}°C'})
    elif temp > 32 or temp < 0:
        factors.append({'name': 'Adverse Temperature', 'severity': 'medium', 'value': f'{temp:.1f}°C'})

    if humidity > 85:
        factors.append({'name': 'Very High Humidity', 'severity': 'medium', 'value': f'{humidity}%'})

    if pressure < 980:
        factors.append({'name': 'Low Pressure System', 'severity': 'high', 'value': f'{pressure} hPa'})
    elif pressure < 1000:
        factors.append({'name': 'Falling Pressure', 'severity': 'medium', 'value': f'{pressure} hPa'})

    if not factors:
        factors.append({'name': 'Normal Conditions', 'severity': 'low', 'value': 'All clear'})

    return factors


def reload_model():
    global _model
    with _model_lock:
        _model = None
    return _get_model() is not None
