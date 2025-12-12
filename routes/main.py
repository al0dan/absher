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
    
    # Calculate Statistics & Insights
    user_cr = session['user'].get('cr')
    user_name = session['user'].get('name')
    
    actions_required = []
    total_value = 0.0
    type_stats = {'supply': 0, 'service': 0, 'nda': 0, 'rental': 0}
    status_stats = {'signed': 0, 'pending': 0}

    for c in contracts:
        # Financials
        try:
            val = float(c.price) if c.price else 0
            total_value += val
        except:
            pass
            
        # Type Distribution
        ctype = c.contract_type or 'general'
        type_stats[ctype] = type_stats.get(ctype, 0) + 1
        
        # Status
        is_completed = c.signed_by_supplier and c.signed_by_buyer
        if is_completed:
            status_stats['signed'] += 1
        else:
            status_stats['pending'] += 1
            
        # Actions Required (If I am a party and haven't signed)
        # Determine my role
        my_role = None
        if c.supplier_cr == user_cr: my_role = 'supplier'
        elif c.buyer_cr == user_cr: my_role = 'buyer'
        
        if my_role == 'supplier' and not c.signed_by_supplier:
            actions_required.append(c)
        elif my_role == 'buyer' and not c.signed_by_buyer:
            actions_required.append(c)

    return render_template('index.html', 
                         user=session['user'], 
                         contracts=contracts,
                         actions_required=actions_required,
                         total_value=total_value,
                         type_stats=type_stats,
                         status_stats=status_stats)

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
