from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO
import os

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
csrf = CSRFProtect()
socketio = SocketIO()


def create_app(config_name=None):
    app = Flask(__name__, template_folder='templates', static_folder='static')

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    from app.config import config_map
    app.config.from_object(config_map.get(config_name, config_map['default']))

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

    from app.auth.routes import auth_bp
    from app.weather.routes import weather_bp
    from app.dashboard.routes import dashboard_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(weather_bp, url_prefix='/api/weather')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return str(user) if not isinstance(user, str) else user

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        from app.auth.models import User
        identity = jwt_data['sub']
        return User.query.filter_by(id=int(identity)).first()

    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    with app.app_context():
        db.create_all()
        _seed_admin()

    from app.sockets import register_events
    register_events(socketio)

    return app


def _seed_admin():
    from app.auth.models import User
    if not User.query.filter_by(email='admin@sentinel.com').first():
        admin = User(username='admin', email='admin@sentinel.com',
                     role='admin', is_active=True, city='New York', alert_threshold=70)
        admin.set_password('Admin@123')
        db.session.add(admin)
        demo = User(username='demo_user', email='user@sentinel.com',
                    role='user', is_active=True, city='Los Angeles', alert_threshold=75)
        demo.set_password('User@123')
        db.session.add(demo)
        db.session.commit()