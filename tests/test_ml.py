import pytest
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_risk_score_range():
    from app.ml.risk_engine import predict_risk
    result = predict_risk(temperature=25, humidity=60, wind_speed=30, pressure=1013)
    assert 0 <= result['score'] <= 100
    assert result['level'] in ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')
    assert result['color'].startswith('#')


def test_risk_score_low_conditions():
    from app.ml.risk_engine import predict_risk
    result = predict_risk(temperature=20, humidity=50, wind_speed=10, pressure=1013)
    assert result['level'] in ('LOW', 'MODERATE')


def test_risk_score_high_wind():
    from app.ml.risk_engine import predict_risk
    result = predict_risk(temperature=25, humidity=60, wind_speed=120, pressure=980)
    assert result['score'] > 50


def test_risk_factors_returned():
    from app.ml.risk_engine import predict_risk
    result = predict_risk(temperature=40, humidity=90, wind_speed=100, pressure=965)
    assert isinstance(result['factors'], list)
    assert len(result['factors']) > 0
    for f in result['factors']:
        assert 'name' in f
        assert 'severity' in f
        assert 'value' in f


def test_risk_description_not_empty():
    from app.ml.risk_engine import predict_risk
    result = predict_risk(temperature=15, humidity=45, wind_speed=20, pressure=1010)
    assert isinstance(result['description'], str)
    assert len(result['description']) > 0


def test_synthetic_data_generation():
    from ml.train_model import generate_synthetic_data
    df = generate_synthetic_data(n_samples=100)
    assert len(df) == 100
    assert set(df.columns) == {'temperature', 'humidity', 'wind_speed', 'pressure', 'risk_score'}
    assert df['risk_score'].between(0, 100).all()


def test_model_training_creates_file():
    import tempfile
    import joblib
    from ml.train_model import generate_synthetic_data
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    df = generate_synthetic_data(n_samples=200)
    X = df[['temperature', 'humidity', 'wind_speed', 'pressure']]
    y = df['risk_score']

    pipe = Pipeline([('scaler', StandardScaler()), ('model', RandomForestRegressor(n_estimators=5, random_state=42))])
    pipe.fit(X, y)

    with tempfile.NamedTemporaryFile(suffix='.joblib', delete=False) as f:
        tmppath = f.name
    try:
        joblib.dump(pipe, tmppath)
        assert os.path.exists(tmppath)
        loaded = joblib.load(tmppath)
        preds = loaded.predict(X[:5])
        assert len(preds) == 5
    finally:
        os.unlink(tmppath)


def test_risk_reload(monkeypatch):
    from app import ml
    result = ml.risk_engine.reload_model()
    assert isinstance(result, bool)
