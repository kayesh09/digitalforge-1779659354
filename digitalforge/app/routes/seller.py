"""
DigitalForge Marketplace - Seller Routes
"""

import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Product, Category, Order
from app.forms import ProductUploadForm
from app.utils.decorators import seller_required
from app.utils.file_handler import save_product_file, save_image_file
from slugify import slugify

bp = Blueprint('seller', __name__)


@bp.route('/dashboard')
@login_required
@seller_required
def dashboard():
    """Seller dashboard"""
    # Get seller's products
    products = Product.query.filter_by(seller_id=current_user.id).order_by(
        Product.created_at.desc()
    ).all()

    # Get sales stats
    sales = Order.query.filter_by(seller_id=current_user.id, payment_status='completed').all()
    total_revenue = sum(float(s.seller_earnings) for s in sales)

    # Recent orders
    recent_orders = Order.query.filter_by(seller_id=current_user.id).order_by(
        Order.created_at.desc()
    ).limit(10).all()

    return render_template('seller/dashboard.html',
                           products=products,
                           sales=sales,
                           total_revenue=total_revenue,
                           recent_orders=recent_orders)


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
@seller_required
def upload_product():
    """Upload new product"""
    form = ProductUploadForm()

    if form.validate_on_submit():
        try:
            # Generate unique slug
            base_slug = slugify(form.title.data)
            slug = base_slug
            counter = 1
            while Product.query.filter_by(slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Save product file
            product_filename, file_size, checksum = save_product_file(
                form.product_file.data,
                current_app.config['PRODUCT_UPLOAD_FOLDER']
            )

            # Save preview images
            preview_images = []
            image_fields = [
                form.preview_image_1, form.preview_image_2, form.preview_image_3,
                form.preview_image_4, form.preview_image_5
            ]

            for field in image_fields:
                if field.data:
                    img_filename, _ = save_image_file(
                        field.data,
                        current_app.config['PRODUCT_UPLOAD_FOLDER']
                    )
                    preview_images.append(img_filename)

            # Create product
            product = Product(
                seller_id=current_user.id,
                category_id=form.category_id.data,
                title=form.title.data,
                slug=slug,
                description=form.description.data,
                short_description=form.short_description.data,
                price=form.price.data,
                file_url=product_filename,
                file_size=file_size,
                file_checksum=checksum,
                preview_images=preview_images,
                demo_url=form.demo_url.data,
                tags=form.tags.data,
                status='active'  # Auto-approve for MVP
            )

            db.session.add(product)

            # Update category count
            category = Category.query.get(form.category_id.data)
            category.product_count = Product.query.filter_by(category_id=category.id, status='active').count()

            db.session.commit()

            flash('Product uploaded successfully!', 'success')
            return redirect(url_for('seller.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading product: {str(e)}', 'danger')

    return render_template('seller/upload.html', form=form)


@bp.route('/product/<int:id>/delete', methods=['POST'])
@login_required
@seller_required
def delete_product(id):
    """Delete a product"""
    product = Product.query.get_or_404(id)

    # Verify ownership
    if product.seller_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this product.', 'danger')
        return redirect(url_for('seller.dashboard'))

    # Archive instead of delete
    product.status = 'archived'
    db.session.commit()

    flash('Product has been archived.', 'info')
    return redirect(url_for('seller.dashboard'))