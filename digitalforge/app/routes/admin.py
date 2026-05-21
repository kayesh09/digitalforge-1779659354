"""
DigitalForge Marketplace - Admin Routes
"""

from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required
from sqlalchemy import func
from app import db
from app.models import User, Product, Order, Category, Payout
from app.utils.decorators import admin_required

bp = Blueprint('admin', __name__)


@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Stats
    stats = {
        'total_users': User.query.count(),
        'total_products': Product.query.count(),
        'total_orders': Order.query.filter_by(payment_status='completed').count(),
        'total_revenue': db.session.query(func.sum(Order.platform_fee)).scalar() or 0,
        'pending_payouts': Payout.query.filter_by(status='pending').count()
    }

    # Recent activity
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(10).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_orders=recent_orders,
                           recent_products=recent_products,
                           recent_users=recent_users)


@bp.route('/products')
@login_required
@admin_required
def products():
    """Admin product management"""
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products)


@bp.route('/orders')
@login_required
@admin_required
def orders():
    """Admin order management"""
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)


@bp.route('/users')
@login_required
@admin_required
def users():
    """Admin user management"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@bp.route('/payouts')
@login_required
@admin_required
def payouts():
    """Admin payout management"""
    payouts = Payout.query.order_by(Payout.created_at.desc()).all()
    return render_template('admin/payouts.html', payouts=payouts)