"""
API endpoints for Web3 interactions and AJAX requests.
"""
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models import Product, Purchase
from app import db
from decimal import Decimal
import json

api_bp = Blueprint('api', __name__)

@api_bp.route('/product/<int:product_id>/price')
def get_product_price(product_id):
    """Get product price in wei for smart contract interaction."""
    product = Product.query.get_or_404(product_id)

    # Convert USD price to ETH (simplified - use oracle in production)
    # For MVP: Assume 1 ETH = $2000 USD
    eth_price = float(product.price) / 2000
    wei_price = int(eth_price * 10**18)

    return jsonify({
        'product_id': product.id,
        'price_usd': str(product.price),
        'price_eth': eth_price,
        'price_wei': wei_price,
        'seller_address': product.seller.wallet_address,
        'contract_address': current_app.config['CONTRACT_ADDRESS']
    })

@api_bp.route('/purchase/verify', methods=['POST'])
@login_required
def verify_purchase():
    """
    Verify blockchain transaction and create purchase record.
    Called by frontend after successful smart contract payment.
    """
    data = request.get_json()

    tx_hash = data.get('tx_hash')
    product_id = data.get('product_id')
    amount = data.get('amount')  # In ETH
    block_number = data.get('block_number')

    if not all([tx_hash, product_id, amount]):
        return jsonify({'error': 'Missing required fields'}), 400

    product = Product.query.get_or_404(product_id)

    # Check for duplicate transaction
    existing = Purchase.query.filter_by(tx_hash=tx_hash).first()
    if existing:
        return jsonify({'error': 'Transaction already processed'}), 409

    # Calculate fee split
    total = Decimal(str(amount))
    platform_fee = total * Decimal('0.15')
    seller_amount = total - platform_fee

    # Create purchase record
    purchase = Purchase(
        buyer_id=current_user.id,
        product_id=product.id,
        seller_id=product.seller_id,
        amount=total,
        platform_fee=platform_fee,
        seller_amount=seller_amount,
        tx_hash=tx_hash,
        block_number=block_number,
        chain_id=current_app.config['CHAIN_ID'],
        status='completed',
        completed_at=db.func.now()
    )

    # Update product stats
    product.sales_count += 1

    db.session.add(purchase)
    db.session.commit()

    return jsonify({
        'success': True,
        'purchase_id': purchase.id,
        'download_url': url_for('product.download', slug=product.slug, _external=True)
    })

@api_bp.route('/user/wallet', methods=['PUT'])
@login_required
def update_wallet():
    """Update user's connected wallet address."""
    data = request.get_json()
    wallet_address = data.get('wallet_address', '').strip()

    if not wallet_address or not wallet_address.startswith('0x'):
        return jsonify({'error': 'Invalid wallet address'}), 400

    # Check if wallet is already linked
    existing = User.query.filter(
        User.wallet_address == wallet_address,
        User.id != current_user.id
    ).first()

    if existing:
        return jsonify({'error': 'Wallet already linked to another account'}), 409

    current_user.wallet_address = wallet_address
    db.session.commit()

    return jsonify({'success': True, 'wallet_address': wallet_address})

@api_bp.route('/search/suggestions')
def search_suggestions():
    """AJAX search suggestions for autocomplete."""
    query = request.args.get('q', '').strip()

    if len(query) < 2:
        return jsonify([])

    products = Product.query.filter(
        Product.title.ilike(f'%{query}%'),
        Product.status == 'active'
    ).limit(5).all()

    return jsonify([{
        'id': p.id,
        'title': p.title,
        'slug': p.slug,
        'price': str(p.price),
        'thumbnail': p.preview_images[0] if p.preview_images else None
    } for p in products])