"""
Configuration classes for different environments.
Uses environment variables for secrets (never hardcode in production).
"""
import os
from datetime import timedelta


class Config:
    """Base configuration shared across all environments."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database - SQLite for dev, PostgreSQL for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///digitalforge.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads - 100MB max per file
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER_PRODUCTS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          'static', 'uploads', 'products')
    UPLOAD_FOLDER_PREVIEWS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          'static', 'uploads', 'previews')

    # Allowed file extensions
    ALLOWED_PRODUCT_EXTENSIONS = {'zip', 'rar', '7z', 'tar', 'gz'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Crypto/Web3 settings
    CHAIN_ID = int(os.environ.get('CHAIN_ID', 8453))  # Base mainnet
    RPC_URL = os.environ.get('RPC_URL', 'https://mainnet.base.org')
    CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS', '')
    PLATFORM_FEE_PERCENT = 15  # 15% commission

    # Mail settings (for future email verification)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries


class ProductionConfig(Config):
    """Production configuration - strict security settings."""
    DEBUG = False
    # Force PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False