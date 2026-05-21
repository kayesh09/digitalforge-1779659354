"""
SQLAlchemy models for DigitalForge Marketplace.
All models include created_at/updated_at timestamps for audit trails.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import uuid

class User(UserMixin, db.Model):
    """User model - can be buyer, seller, or both."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)

    # Profile
    display_name = db.Column(db.String(120))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(500))
    wallet_address = db.Column(db.String(42), unique=True, index=True)  # ETH address

    # Role flags
    is_seller = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)

    # Crypto payout info
    preferred_payout_chain = db.Column(db.String(20), default='base')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    products = db.relationship('Product', backref='seller', lazy='dynamic',
                              foreign_keys='Product.seller_id')
    purchases = db.relationship('Purchase', backref='buyer', lazy='dynamic',
                                foreign_keys='Purchase.buyer_id')

    def set_password(self, password):
        """Hash and store password securely."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def get_total_sales(self):
        """Calculate total sales amount for seller dashboard."""
        return db.session.query(db.func.sum(Purchase.amount)).\
            filter(Purchase.product_id.in_([p.id for p in self.products])).\
            scalar() or 0

    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):
    """Product categories for browsing and filtering."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(50))  # FontAwesome or Lucide icon name
    product_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    """Digital product listing."""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(300))

    # Pricing
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Stored in USD equivalent
    currency = db.Column(db.String(10), default='ETH')
    is_free = db.Column(db.Boolean, default=False)

    # Categorization
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    category = db.relationship('Category', backref='products')
    tags = db.Column(db.String(500))  # Comma-separated tags

    # File handling
    file_path = db.Column(db.String(500), nullable=False)  # Server path to encrypted file
    file_size = db.Column(db.BigInteger)  # Bytes
    file_name = db.Column(db.String(255))  # Original filename
    file_extension = db.Column(db.String(10))
    encryption_iv = db.Column(db.String(255))  # Initialization vector for decryption
    ipfs_hash = db.Column(db.String(100))  # Future IPFS integration

    # Preview media
    preview_images = db.Column(db.JSON, default=list)  # Array of image paths
    demo_url = db.Column(db.String(500))  # Live demo link
    video_url = db.Column(db.String(500))  # Optional video preview

    # Metadata
    version = db.Column(db.String(20), default='1.0')
    requirements = db.Column(db.Text)  # System requirements or dependencies

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, active, rejected, archived
    is_featured = db.Column(db.Boolean, default=False)
    featured_order = db.Column(db.Integer, default=0)

    # Stats
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    sales_count = db.Column(db.Integer, default=0)
    rating_avg = db.Column(db.Numeric(2, 1), default=0)
    rating_count = db.Column(db.Integer, default=0)

    # Foreign keys
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)

    # Relationships
    purchases = db.relationship('Purchase', backref='product', lazy='dynamic')

    def get_price_eth(self):
        """Convert stored price to ETH string for Web3."""
        return str(self.price)

    def increment_views(self):
        """Thread-safe view counter increment."""
        self.view_count += 1
        db.session.commit()

    def __repr__(self):
        return f'<Product {self.title}>'


class Purchase(db.Model):
    """Purchase record linking buyer to product with transaction details."""
    __tablename__ = 'purchases'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))

    # Foreign keys
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Transaction details
    amount = db.Column(db.Numeric(10, 6), nullable=False)  # Amount paid in ETH
    platform_fee = db.Column(db.Numeric(10, 6), nullable=False)  # 15% fee
    seller_amount = db.Column(db.Numeric(10, 6), nullable=False)  # 85% to seller

    # Blockchain
    tx_hash = db.Column(db.String(66), unique=True, nullable=False, index=True)
    block_number = db.Column(db.BigInteger)
    chain_id = db.Column(db.Integer)

    # Status
    status = db.Column(db.String(20), default='completed')  # pending, completed, refunded, disputed

    # Download tracking
    download_count = db.Column(db.Integer, default=0)
    last_downloaded = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Purchase {self.uuid}>'


class Review(db.Model):
    """Product reviews and ratings."""
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(100))
    body = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', backref='reviews')
    user = db.relationship('User', backref='reviews')


class Payout(db.Model):
    """Seller payout records."""
    __tablename__ = 'payouts'

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 6), nullable=False)
    tx_hash = db.Column(db.String(66), unique=True)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)