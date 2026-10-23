from flask import Blueprint, render_template, redirect, url_for, request, jsonify, make_response
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, jwt_required
from app import db, csrf
from app.auth.models import User, SystemLog
from datetime import datetime
import html

auth_bp = Blueprint('auth', __name__)


def log_action(user_id, action, level='INFO', details=None):
    log = SystemLog(
        user_id=user_id,
        action=action,
        level=level,
        details=details,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()


@auth_bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
    error = None
    if request.method == 'POST':
        email = html.escape(request.form.get('email', '').strip().lower())
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password) and user.is_active:
            user.last_login = datetime.utcnow()
            db.session.commit()
            access_token = create_access_token(identity=str(user.id))
            response = make_response(redirect(url_for('dashboard.index')))
            set_access_cookies(response, access_token)
            log_action(user.id, 'User login', 'INFO', f'Login from {request.remote_addr}')
            return response
        else:
            log_action(None, f'Failed login attempt for {email}', 'WARNING')
            error = 'Invalid credentials or account disabled.'

    return render_template('auth/login.html', error=error)


@auth_bp.route('/register', methods=['GET', 'POST'])
@csrf.exempt
def register():
    error = None
    form_errors = []
    if request.method == 'POST':
        username = html.escape(request.form.get('username', '').strip())
        email = html.escape(request.form.get('email', '').strip().lower())
        city = html.escape(request.form.get('city', '').strip())
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if password != confirm:
            form_errors.append('Passwords must match.')
        elif len(password) < 8:
            form_errors.append('Password must be at least 8 characters.')
        elif not any(c.isupper() for c in password):
            form_errors.append('Password must contain at least one uppercase letter.')
        elif not any(c.isdigit() for c in password):
            form_errors.append('Password must contain at least one digit.')
        elif User.query.filter_by(email=email).first():
            error = 'Email already registered.'
        elif User.query.filter_by(username=username).first():
            error = 'Username already taken.'
        else:
            user = User(username=username, email=email, city=city, role='user')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            log_action(user.id, 'New user registration', 'INFO')
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html', error=error, form_errors=form_errors)


@auth_bp.route('/logout')
def logout():
    response = make_response(redirect(url_for('auth.login')))
    unset_jwt_cookies(response)
    return response


@auth_bp.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    from flask_jwt_extended import current_user
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    user = current_user
    if 'username' in data:
        username = html.escape(data['username'].strip())
        existing = User.query.filter_by(username=username).first()
        if existing and existing.id != user.id:
            return jsonify({'error': 'Username already taken'}), 400
        user.username = username
    if 'city' in data:
        user.city = html.escape(data['city'].strip())
    if 'alert_threshold' in data:
        threshold = int(data['alert_threshold'])
        if 0 <= threshold <= 100:
            user.alert_threshold = threshold
    if 'email_alerts' in data:
        user.email_alerts = bool(data['email_alerts'])

    db.session.commit()
    log_action(user.id, 'Profile updated', 'INFO')
    return jsonify({'message': 'Profile updated', 'user': user.to_dict()})