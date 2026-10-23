"""
Train a Random Forest model for disaster risk prediction.
Run: python ml/train_model.py
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

RANDOM_STATE = 42
N_SAMPLES = 5000
MODEL_OUTPUT = os.path.join(os.path.dirname(__file__), 'model.joblib')


def generate_synthetic_data(n_samples=N_SAMPLES):
    np.random.seed(RANDOM_STATE)

    temperature = np.random.uniform(-10, 50, n_samples)
    humidity = np.random.uniform(10, 100, n_samples)
    wind_speed = np.random.uniform(0, 150, n_samples)
    pressure = np.random.uniform(950, 1050, n_samples)

    risk_score = (
        np.clip((temperature - 20) / 30 * 25, 0, 25) +
        np.clip((humidity - 50) / 50 * 20, 0, 20) +
        np.clip(wind_speed / 150 * 35, 0, 35) +
        np.clip((1013 - pressure) / 63 * 20, 0, 20)
    )

    noise = np.random.normal(0, 3, n_samples)
    risk_score = np.clip(risk_score + noise, 0, 100)

    df = pd.DataFrame({
        'temperature': temperature,
        'humidity': humidity,
        'wind_speed': wind_speed,
        'pressure': pressure,
        'risk_score': risk_score
    })
    return df


def train():
    print("Generating synthetic training data...")
    df = generate_synthetic_data()

    X = df[['temperature', 'humidity', 'wind_speed', 'pressure']]
    y = df['risk_score']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('model', RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=RANDOM_STATE,
            n_jobs=-1
        ))
    ])

    print("Training Random Forest model...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"Model Performance:")
    print(f"  MSE:  {mse:.4f}")
    print(f"  RMSE: {np.sqrt(mse):.4f}")
    print(f"  R²:   {r2:.4f}")

    os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)
    joblib.dump(pipeline, MODEL_OUTPUT)
    print(f"Model saved to: {MODEL_OUTPUT}")

    return {'mse': mse, 'rmse': float(np.sqrt(mse)), 'r2': r2}


if __name__ == '__main__':
    metrics = train()
    print("\nTraining complete!")
    print(f"Final R² Score: {metrics['r2']:.4f}")
