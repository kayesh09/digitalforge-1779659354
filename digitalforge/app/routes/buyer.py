"""
DigitalForge Marketplace - Buyer Routes
"""

from flask import Blueprint, render_template, send_from_directory, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app import db
from app.models import Order, Product
from app.utils.decorators import seller_required
import os

bp = Blueprint('buyer', __name__)


@bp.route('/dashboard')
@login_required
def dashboard():
    """Buyer dashboard - My purchases"""
    orders = Order.query.filter_by(buyer_id=current_user.id).order_by(
        Order.created_at.desc()
    ).all()

    return render_template('buyer/dashboard.html', orders=orders)


@bp.route('/download/<token>')
@login_required
def download_file(token):
    """Secure file download"""
    order = Order.query.filter_by(download_token=token).first_or_404()

    # Verify ownership
    if order.buyer_id != current_user.id and not current_user.is_admin:
        abort(403)

    # Check if download is valid
    if not order.is_download_valid():
        flash('Download link has expired or is invalid.', 'danger')
        return redirect(url_for('buyer.dashboard'))

    # Increment download count
    order.download_count += 1
    db.session.commit()

    # Send file
    product = Product.query.get(order.product_id)
    file_path = os.path.join(current_app.root_path, 'static', 'uploads', 'products')

    return send_from_directory(
        file_path,
        product.file_url,
        as_attachment=True,
        download_name=f"{product.slug}.zip"
    )