"""
DigitalForge Marketplace - Application Factory
Production-ready Flask app with SQLAlchemy, LoginManager, and Migrate
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from dotenv import load_dotenv
import os

# Initialize extensions (no app yet)
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()

def create_app(config_name='development'):
    """Application factory pattern for better testability and config management."""
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    app.config.from_object(f'app.config.{config_name.capitalize()}Config')

    # Ensure upload directories exist
    os.makedirs(app.config['UPLOAD_FOLDER_PRODUCTS'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_PREVIEWS'], exist_ok=True)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Login settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # ====== ADD THIS USER LOADER ======
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login sessions."""
        return User.query.get(int(user_id))
    # ===================================

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.product import product_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(product_bp, url_prefix='/product')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Create tables if they don't exist (dev only, use migrations in prod)
    with app.app_context():
        db.create_all()

    return app