"""
Main public routes: homepage, product listing, search, about.
"""
from flask import Blueprint, render_template, request, current_app
from sqlalchemy import or_, func
from app.models import Product, Category, User
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage with featured products, categories, and stats."""
    # Featured products (admin curated)
    featured = Product.query.filter_by(status='active', is_featured=True).\
        order_by(Product.featured_order.asc()).limit(6).all()

    # New arrivals
    new_arrivals = Product.query.filter_by(status='active').\
        order_by(Product.created_at.desc()).limit(8).all()

    # Popular products (by sales)
    popular = Product.query.filter_by(status='active').\
        order_by(Product.sales_count.desc()).limit(6).all()

    # Categories with counts
    categories = Category.query.order_by(Category.name).all()

    # Platform stats
    stats = {
        'total_products': Product.query.filter_by(status='active').count(),
        'total_creators': User.query.filter_by(is_seller=True).count(),
        'total_sales': db.session.query(func.sum(Product.sales_count)).scalar() or 0
    }

    return render_template('index.html',
                        featured=featured,
                        new_arrivals=new_arrivals,
                        popular=popular,
                        categories=categories,
                        stats=stats)

@main_bp.route('/products')
def product_list():
    """Product listing page with filters and pagination."""
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('category', '')
    search_query = request.args.get('q', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort = request.args.get('sort', 'newest')  # newest, popular, price_low, price_high

    # Base query
    query = Product.query.filter_by(status='active')

    # Apply filters
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first()
        if category:
            query = query.filter_by(category_id=category.id)

    if search_query:
        search_filter = or_(
            Product.title.ilike(f'%{search_query}%'),
            Product.description.ilike(f'%{search_query}%'),
            Product.tags.ilike(f'%{search_query}%')
        )
        query = query.filter(search_filter)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Apply sorting
    if sort == 'popular':
        query = query.order_by(Product.sales_count.desc())
    elif sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())

    # Paginate
    pagination = query.paginate(
        page=page,
        per_page=current_app.config.get('PRODUCTS_PER_PAGE', 20),
        error_out=False
    )

    products = pagination.items
    categories = Category.query.order_by(Category.name).all()

    return render_template('product_list.html',
                        products=products,
                        pagination=pagination,
                        categories=categories,
                        current_category=category_slug,
                        search_query=search_query,
                        sort=sort)

@main_bp.route('/category/<slug>')
def category_detail(slug):
    """Category detail page."""
    category = Category.query.filter_by(slug=slug).first_or_404()
    products = Product.query.filter_by(
        category_id=category.id,
        status='active'
    ).order_by(Product.created_at.desc()).all()

    return render_template('category.html', category=category, products=products)

@main_bp.route('/seller/<username>')
def seller_profile(username):
    """Public seller profile page."""
    seller = User.query.filter_by(username=username, is_seller=True).first_or_404()
    products = Product.query.filter_by(
        seller_id=seller.id,
        status='active'
    ).order_by(Product.created_at.desc()).all()

    return render_template('seller_profile.html', seller=seller, products=products)