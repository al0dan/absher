from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps
from models import Contract
from database import db
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    user_cr = session['user'].get('cr')
    
    # Filter contracts where user is supplier OR buyer (matching by CR)
    # Using SQLAlchemy ORM
    contracts = Contract.query.filter(
        or_(Contract.supplier_cr == user_cr, Contract.buyer_cr == user_cr)
    ).order_by(Contract.created_at.desc()).all()
    
    # Convert SQLAlchemy objects to dicts for template
    contracts_data = [c.to_dict() for c in contracts]
    
    # Add extra fields expected by template that might not be in to_dict
    # The template likely expects direct attribute access if we passed objects, 
    # but let's pass dicts to be safe or objects. 
    # Actually, passing objects is fine for Jinja2.
    
    return render_template('index.html', user=session['user'], contracts=contracts)

@main_bp.route('/service')
def service_page():
    return render_template('service.html')

@main_bp.route('/api/contracts')
@login_required
def get_contracts_api():
    user = session.get('user', {})
    cr = user.get('cr')
    
    if not cr:
        return jsonify([])
        
    contracts = Contract.query.filter((Contract.supplier_cr == cr) | (Contract.buyer_cr == cr)).all()
    
    return jsonify([{
        'id': c.id,
        'supplier': c.supplier,
        'buyer': c.buyer,
        'price': c.price,
        'status': 'active' # Placeholder
    } for c in contracts])

@main_bp.route('/health')
def health():
    return {"status": "healthy"}

@main_bp.route('/metrics')
def metrics():
    count = Contract.query.count()
    return {'total_contracts': count, 'uptime': '99.9%'}
