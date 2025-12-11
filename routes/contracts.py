import uuid
import logging
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, Response, current_app
from functools import wraps
import bleach

from models import Contract, User
from database import db
from services.ai_service import generate_contract_ai
from services.pdf_service import generate_contract_pdf 

contracts_bp = Blueprint('contracts', __name__)
logger = logging.getLogger(__name__)

# --- Helpers ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        # Check config
        valid_key = current_app.config.get('API_KEY') or 'dev_api_key'
        if key and key == valid_key:
            return f(*args, **kwargs)
        logger.warning(f"Unauthorized API access attempt from {request.remote_addr}")
        return jsonify({'error': 'Unauthorized'}), 401
    return decorated_function

def sanitize_input(text):
    if not isinstance(text, str):
        return text
    return bleach.clean(text, tags=[], strip=True)

def validate_vat_number(vat: str) -> dict:
    result = {'valid': False, 'error': None}
    if not vat:
        result['error'] = 'VAT number is required'
        return result
    vat = vat.replace(' ', '').replace('-', '')
    if not vat.isdigit():
        result['error'] = 'VAT number must contain only digits'
        return result
    if len(vat) != 15:
        result['error'] = 'VAT number must be 15 digits'
        return result
    if not vat.startswith('3'):
        result['error'] = 'Saudi VAT must start with 3'
        return result
    if not vat.endswith('3'):
        result['error'] = 'Saudi VAT must end with 3'
        return result
    result['valid'] = True
    result['formatted'] = vat
    return result

def validate_cr_number(cr: str) -> dict:
    result = {'valid': False, 'error': None}
    if not cr:
        result['error'] = 'CR number is required'
        return result
    cr = cr.replace(' ', '').replace('-', '')
    if not cr.isdigit():
        result['error'] = 'CR number must contain only digits'
        return result
    if len(cr) != 10:
        result['error'] = 'CR number must be 10 digits'
        return result
    region_codes = {'1': 'Riyadh', '2': 'Makkah', '3': 'Madinah', '4': 'Eastern', '5': 'Qassim', '6': 'Asir'}
    region = region_codes.get(cr[0], 'Unknown')
    result['valid'] = True
    result['formatted'] = cr
    result['region'] = region
    return result

# --- Routes ---

@contracts_bp.route('/create')
@login_required
def create_page():
    return render_template('create_contract.html', API_KEY=current_app.config.get('API_KEY'), user=session.get('user', {}))

@contracts_bp.route('/contract/<token_or_id>')
def view_contract(token_or_id):
    contract = Contract.query.get(token_or_id)
    if not contract:
        contract = Contract.query.filter((Contract.supplier_token == token_or_id) | (Contract.buyer_token == token_or_id)).first()
    
    if not contract:
        return render_template('contract-view.html', error=True, contract_id=token_or_id)
    
    c_dict = contract.__dict__.copy()
    c_dict.pop('_sa_instance_state', None)
    
    if 'user' not in session:
        return redirect(url_for('auth.login_page', next=request.path))
        
    current_user_cr = session['user'].get('cr')
    view_role = 'public' 
    
    if current_user_cr == contract.supplier_cr:
        view_role = 'supplier'
    elif current_user_cr == contract.buyer_cr:
        view_role = 'buyer'
        
    return render_template('contract-view.html', error=False, contract=c_dict, view_role=view_role, API_KEY=current_app.config.get('API_KEY'))

@contracts_bp.route('/contract/<contract_id>/pdf')
def download_contract_pdf_route(contract_id):
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return jsonify({'error': 'Contract not found'}), 404
            
        c_dict = contract.__dict__.copy()
        c_dict.pop('_sa_instance_state', None)
        
        pdf_bytes = generate_contract_pdf(c_dict)
        
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=contract_{contract_id}.pdf'
            }
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return jsonify({'error': str(e)}), 500

# --- Validation API ---

@contracts_bp.route('/api/validate/vat', methods=['POST'])
def validate_vat_api():
    data = request.json or {}
    vat = data.get('vat', '')
    result = validate_vat_number(vat)
    return jsonify(result)

@contracts_bp.route('/api/validate/cr', methods=['POST'])
def validate_cr_api():
    data = request.json or {}
    cr = data.get('cr', '')
    result = validate_cr_number(cr)
    return jsonify(result)

@contracts_bp.route('/api/validate/both', methods=['POST'])
def validate_both_api():
    data = request.json or {}
    vat_result = validate_vat_number(data.get('vat', ''))
    cr_result = validate_cr_number(data.get('cr', ''))
    return jsonify({
        'vat': vat_result,
        'cr': cr_result,
        'all_valid': vat_result['valid'] and cr_result['valid']
    })

@contracts_bp.route('/api/lookup/cr', methods=['POST'])
def lookup_cr_api():
    data = request.json or {}
    cr = data.get('cr', '').strip()
    
    if not cr:
        return jsonify({'found': False, 'error': 'CR required'}), 400
        
    user = User.query.filter_by(cr_number=cr).first()
    
    if user:
        return jsonify({
            'found': True,
            'company_name': user.company_name,
            'vat_number': user.vat_number
        })
    return jsonify({'found': False})

# --- Contract API ---

@contracts_bp.route('/api/contract', methods=['POST'])
@require_api_key
def create_contract_api():
    try:
        data = request.json
        supplier = sanitize_input(data.get('supplier', ''))
        buyer = sanitize_input(data.get('buyer', ''))
        supplier_vat = sanitize_input(data.get('supplier_vat', ''))
        buyer_vat = sanitize_input(data.get('buyer_vat', ''))
        supplier_cr = sanitize_input(data.get('supplier_cr', ''))
        buyer_cr = sanitize_input(data.get('buyer_cr', ''))
        items = sanitize_input(data.get('items', ''))
        price = data.get('price', 0)

        errors = []
        if len(supplier) < 3: errors.append("Provider name too short")
        if len(buyer) < 3: errors.append("Buyer name too short")
        if len(items) < 10: errors.append("Items description too short")
        
        vat_res = validate_vat_number(supplier_vat)
        if supplier_vat and not vat_res['valid']: errors.append(f"Supplier VAT: {vat_res['error']}")
        
        buyer_vat_res = validate_vat_number(buyer_vat)
        if buyer_vat and not buyer_vat_res['valid']: errors.append(f"Buyer VAT: {buyer_vat_res['error']}")

        try:
            price = float(price)
            if price < 0.01: errors.append("Price invalid")
        except:
            errors.append("Price invalid format")

        if errors:
            return jsonify({'error': 'validation_error', 'messages': errors}), 400
        
        contract_text = generate_contract_ai(supplier, buyer, items, price)
        
        new_contract = Contract(
            id=str(uuid.uuid4())[:8],
            supplier=supplier,
            buyer=buyer,
            supplier_vat=supplier_vat,
            buyer_vat=buyer_vat,
            supplier_cr=supplier_cr,
            buyer_cr=buyer_cr,
            items=items,
            price=price,
            contract_text=contract_text,
            supplier_token=str(uuid.uuid4()),
            buyer_token=str(uuid.uuid4())
        )
        
        db.session.add(new_contract)
        db.session.commit()
        
        return jsonify({
            'id': new_contract.id,
            'supplier_url': f'http://{request.host}/contract/{new_contract.supplier_token}',
            'buyer_url': f'http://{request.host}/contract/{new_contract.buyer_token}'
        })
    except Exception as e:
        logger.critical(f"System Error: {e}")
        return jsonify({'error': 'System error', 'message': str(e)}), 500

@contracts_bp.route('/api/contract/<contract_id>/sign', methods=['POST'])
@require_api_key
def sign_contract_api(contract_id):
    data = request.json
    role = data.get('role')
    name = sanitize_input(data.get('name'))
    signature_data = data.get('signature_data')
    
    contract = Contract.query.get(contract_id)
    if not contract:
        return jsonify({'error': 'not_found'}), 404
        
    if role == 'supplier':
        contract.signed_by_supplier = True
        contract.supplier_name = name
        contract.supplier_signature = signature_data
    elif role == 'buyer':
        contract.signed_by_buyer = True
        contract.buyer_name = name
        contract.buyer_signature = signature_data
    
    db.session.commit()
    return jsonify({'status': 'signed'})
