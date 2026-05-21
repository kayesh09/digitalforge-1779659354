"""
Authentication routes: login, register, logout.
Uses Flask-Login for session management and Werkzeug for password hashing.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from urllib.parse import urlparse

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        wallet_address = request.form.get('wallet_address', '').strip()

        # Validation
        errors = []
        if not email or '@' not in email:
            errors.append('Valid email is required.')
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        # Check uniqueness
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken.')
        if wallet_address and User.query.filter_by(wallet_address=wallet_address).first():
            errors.append('Wallet address already linked to another account.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html',
                                 email=email, username=username, wallet=wallet_address), 400

        # Create user
        user = User(
            email=email,
            username=username,
            wallet_address=wallet_address if wallet_address else None,
            is_seller=request.form.get('become_seller') == 'on'
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = db.func.now()
            db.session.commit()

            # Redirect to requested page or dashboard
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('main.index')
            return redirect(next_page)

        flash('Invalid email or password.', 'danger')
        return render_template('login.html', email=email), 401

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Update user profile."""
    if request.method == 'POST':
        current_user.display_name = request.form.get('display_name', '').strip()
        current_user.bio = request.form.get('bio', '').strip()
        current_user.wallet_address = request.form.get('wallet_address', '').strip() or None

        # Toggle seller status
        if request.form.get('become_seller') == 'on' and not current_user.is_seller:
            current_user.is_seller = True

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('profile.html')