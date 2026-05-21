"""
DigitalForge Marketplace - Custom Decorators
"""

from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def seller_required(f):
    """Decorator to require seller role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.path))
        if not current_user.is_seller and not current_user.is_admin:
            flash('You need to be a seller to access this page.', 'warning')
            return redirect(url_for('main.become_seller'))
        return f(*args, **kwargs)
    return decorated_function