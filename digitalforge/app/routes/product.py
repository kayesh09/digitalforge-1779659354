"""
Product detail, purchase, and download routes.
Handles crypto payment verification and secure file delivery.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, \
    current_app, send_file, abort
from flask_login import login_required, current_user
from app.models import Product, Purchase, Category
from app import db
from app.utils.file_handler import allowed_file, save_preview_images
import os
import secrets

product_bp = Blueprint('product', __name__)

@product_bp.route('/<slug>')
def detail(slug):
    """Product detail page with preview and purchase options."""
    product = Product.query.filter_by(slug=slug, status='active').first_or_404()

    # Increment view count
    product.view_count += 1
    db.session.commit()

    # Check if current user has purchased this
    has_purchased = False
    if current_user.is_authenticated:
        has_purchased = Purchase.query.filter_by(
            buyer_id=current_user.id,
            product_id=product.id,
            status='completed'
        ).first() is not None

    # Related products (same category, excluding current)
    from sqlalchemy import func
    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.status == 'active'
    ).order_by(func.random()).limit(4).all()

    return render_template('product_detail.html',
                        product=product,
                        has_purchased=has_purchased,
                        related_products=related)

@product_bp.route('/<slug>/download')
@login_required
def download(slug):
    """
    Secure file download for verified purchasers.
    """
    product = Product.query.filter_by(slug=slug).first_or_404()

    # Verify purchase
    purchase = Purchase.query.filter_by(
        buyer_id=current_user.id,
        product_id=product.id,
        status='completed'
    ).first()

    if not purchase and not current_user.is_admin and product.seller_id != current_user.id:
        flash('You must purchase this product before downloading.', 'warning')
        return redirect(url_for('product.detail', slug=slug))

    # Update download stats
    purchase.download_count += 1
    purchase.last_downloaded = db.func.now()
    product.download_count += 1
    db.session.commit()

    # Serve file
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER_PRODUCTS'], product.file_path)

    if not os.path.exists(file_path):
        abort(404, 'File not found on server.')

    response = send_file(
        file_path,
        as_attachment=True,
        download_name=product.file_name or f"{product.slug}.zip"
    )
    response.headers['X-Decryption-IV'] = product.encryption_iv
    return response

@product_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Seller product upload with client-side encryption."""
    if not current_user.is_seller:
        flash('You need to enable seller mode to upload products.', 'warning')
        return redirect(url_for('auth.profile'))

    if request.method == 'POST':
        # Basic validation
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', type=float)
        category_id = request.form.get('category', type=int)
        demo_url = request.form.get('demo_url', '').strip()
        tags = request.form.get('tags', '').strip()

        # File handling
        product_file = request.files.get('product_file')
        preview_images = request.files.getlist('preview_images')

        errors = []
        if not title or len(title) < 5:
            errors.append('Title must be at least 5 characters.')
        if not description or len(description) < 20:
            errors.append('Description must be at least 20 characters.')
        if price is None or price < 0:
            errors.append('Price must be 0 or greater.')
        if not category_id:
            errors.append('Please select a category.')
        if not product_file:
            errors.append('Product file is required.')
        elif not allowed_file(product_file.filename, 'product'):
            errors.append('Invalid file type. Use ZIP, RAR, 7Z, TAR, or GZ.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('upload_product.html'), 400

        # Generate unique slug
        base_slug = title.lower().replace(' ', '-')[:50]
        slug = base_slug
        counter = 1
        while Product.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Save encrypted product file
        file_ext = product_file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{secrets.token_hex(8)}_{slug}.{file_ext}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER_PRODUCTS'], unique_filename)

        # Get encryption IV from form (set by client-side JS)
        encryption_iv = request.form.get('encryption_iv', '')

        product_file.save(file_path)

        # Save preview images
        saved_previews = save_preview_images(preview_images, slug, current_app)

        # Create product record
        product = Product(
            title=title,
            slug=slug,
            description=description,
            short_description=description[:150] + '...' if len(description) > 150 else description,
            price=price,
            category_id=category_id,
            seller_id=current_user.id,
            file_path=unique_filename,
            file_size=os.path.getsize(file_path),
            file_name=product_file.filename,
            file_extension=file_ext,
            encryption_iv=encryption_iv,
            demo_url=demo_url if demo_url else None,
            tags=tags,
            status='active' if current_user.is_verified else 'pending'
        )

        if saved_previews:
            product.preview_images = saved_previews

        db.session.add(product)
        db.session.commit()

        flash('Product uploaded successfully! It will be live after review.'
              if product.status == 'pending' else 'Product is now live!', 'success')
        return redirect(url_for('dashboard.seller'))

    categories = Category.query.order_by(Category.name).all()
    return render_template('upload_product.html', categories=categories)