"""
Dashboard routes for buyers and sellers.
"""
from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Product, Purchase, Payout
from app import db

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/seller')
@login_required
def seller():
    """Seller dashboard with products, sales, and analytics."""
    if not current_user.is_seller:
        flash('You are not registered as a seller.', 'warning')
        return redirect(url_for('main.index'))

    # Seller's products
    products = Product.query.filter_by(seller_id=current_user.id). \
        order_by(Product.created_at.desc()).all()

    # Sales data
    sales = Purchase.query.filter(
        Purchase.product_id.in_([p.id for p in products]),
        Purchase.status == 'completed'
    ).order_by(Purchase.created_at.desc()).all()

    # Calculate earnings
    total_earnings = sum(float(s.seller_amount) for s in sales)
    pending_payout = sum(float(s.seller_amount) for s in sales if not s.completed_at)

    # Monthly stats (last 6 months)
    from datetime import datetime, timedelta
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_sales = db.session.query(
        db.func.strftime('%Y-%m', Purchase.created_at).label('month'),
        db.func.sum(Purchase.seller_amount).label('total')
    ).filter(
        Purchase.product_id.in_([p.id for p in products]),
        Purchase.created_at >= six_months_ago
    ).group_by('month').order_by('month').all()

    return render_template('seller_dashboard.html',
                           products=products,
                           sales=sales,
                           total_earnings=total_earnings,
                           pending_payout=pending_payout,
                           monthly_sales=monthly_sales)


@dashboard_bp.route('/buyer')
@login_required
def buyer():
    """Buyer dashboard with purchases and downloads."""
    purchases = Purchase.query.filter_by(buyer_id=current_user.id). \
        order_by(Purchase.created_at.desc()).all()

    return render_template('buyer_dashboard.html', purchases=purchases)


@dashboard_bp.route('/admin')
@login_required
def admin():
    """Admin panel for platform management."""
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    # Platform overview
    stats = {
        'total_users': db.session.query(db.func.count(current_user.id)).scalar(),
        'total_products': Product.query.count(),
        'pending_products': Product.query.filter_by(status='pending').count(),
        'total_sales': db.session.query(db.func.sum(Purchase.amount)).scalar() or 0,
        'platform_fees': db.session.query(db.func.sum(Purchase.platform_fee)).scalar() or 0
    }

    pending_products = Product.query.filter_by(status='pending'). \
        order_by(Product.created_at.desc()).all()

    recent_sales = Purchase.query.order_by(Purchase.created_at.desc()).limit(20).all()

    return render_template('admin.html',
                           stats=stats,
                           pending_products=pending_products,
                           recent_sales=recent_sales)