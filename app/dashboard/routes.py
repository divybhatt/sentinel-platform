from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import current_user, verify_jwt_in_request
from functools import wraps

dashboard_bp = Blueprint('dashboard', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            print("JWT OK, user:", current_user)
        except Exception as e:
            print("JWT FAILED:", e)
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@dashboard_bp.route('/')
@login_required
def index():
    return render_template('dashboard/index.html', user=current_user, page='dashboard')


@dashboard_bp.route('/forecast')
@login_required
def forecast():
    return render_template('dashboard/forecast.html', user=current_user, page='forecast')


@dashboard_bp.route('/risk-analysis')
@login_required
def risk_analysis():
    return render_template('dashboard/risk_analysis.html', user=current_user, page='risk')


@dashboard_bp.route('/compare')
@login_required
def compare():
    return render_template('dashboard/compare.html', user=current_user, page='compare')


@dashboard_bp.route('/profile')
@login_required
def profile():
    return render_template('dashboard/profile.html', user=current_user, page='profile')