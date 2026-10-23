import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Auto-train model if not present
    model_path = os.path.join(os.path.dirname(__file__), 'ml', 'model.joblib')
    if not os.path.exists(model_path):
        print("Model not found. Training now...")
        try:
            import subprocess
            train_script = os.path.join(os.path.dirname(__file__), 'ml', 'train_model.py')
            subprocess.run([sys.executable, train_script], check=True)
        except Exception as e:
            print(f"Warning: Could not train model: {e}. Using fallback.")

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))
