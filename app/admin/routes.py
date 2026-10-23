from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_jwt_extended import current_user, verify_jwt_in_request
from functools import wraps
from app import db
from app.auth.models import User, SystemLog
import subprocess
import sys
import os

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return redirect(url_for('auth.login'))
        if not current_user or not current_user.is_admin():
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@admin_required
def panel():
    users = User.query.all()
    logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(50).all()
    return render_template('admin/panel.html', user=current_user, users=users,
                           logs=logs, page='admin')


@admin_bp.route('/api/users')
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@admin_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    if 'is_active' in data:
        user.is_active = bool(data['is_active'])
    if 'role' in data and data['role'] in ['user', 'admin']:
        user.role = data['role']
    db.session.commit()
    _log(current_user.id, f'Updated user {user.username}', 'INFO')
    return jsonify({'message': 'User updated', 'user': user.to_dict()})


@admin_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    user = User.query.get_or_404(user_id)
    username = user.username
    SystemLog.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    _log(current_user.id, f'Deleted user {username}', 'WARNING')
    return jsonify({'message': 'User deleted'})


@admin_bp.route('/api/retrain', methods=['POST'])
@admin_required
def retrain_model():
    try:
        train_script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'ml', 'train_model.py'
        )
        result = subprocess.run(
            [sys.executable, train_script],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            from app.ml.risk_engine import reload_model
            reload_model()
            _log(current_user.id, 'ML model retrained successfully', 'INFO', result.stdout)
            return jsonify({'message': 'Model retrained successfully', 'output': result.stdout})
        else:
            _log(current_user.id, 'ML model retraining failed', 'ERROR', result.stderr)
            return jsonify({'error': 'Retraining failed', 'output': result.stderr}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Training timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/logs')
@admin_required
def get_logs():
    page = request.args.get('page', 1, type=int)
    level = request.args.get('level', '')
    logs_query = SystemLog.query.order_by(SystemLog.timestamp.desc())
    if level:
        logs_query = logs_query.filter_by(level=level)
    logs = logs_query.paginate(page=page, per_page=50, error_out=False)
    return jsonify({
        'logs': [l.to_dict() for l in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': logs.page
    })


@admin_bp.route('/api/stats')
@admin_required
def get_stats():
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_count = User.query.filter_by(role='admin').count()
    log_count = SystemLog.query.count()
    warnings = SystemLog.query.filter_by(level='WARNING').count()
    errors = SystemLog.query.filter_by(level='ERROR').count()
    model_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'ml', 'model.joblib'
    )
    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'admin_count': admin_count,
        'log_count': log_count,
        'warnings': warnings,
        'errors': errors,
        'model_trained': os.path.exists(model_path)
    })


def _log(user_id, action, level='INFO', details=None):
    log = SystemLog(user_id=user_id, action=action, level=level,
                    details=details, ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()