from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app
from models import User
from database import db
from services.nafath_service import get_nafath_redirect, oauth
import uuid


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user'] = {
                'id': user.id,
                'username': user.username,
                'name': user.company_name,
                'name_en': user.company_name_en,
                'cr': user.cr_number,
                'vat': user.vat_number,
                'unified': user.unified_number,
                'city': user.city,
                'type': user.user_type
            }
            session.permanent = True
            return redirect(url_for('main.dashboard'))
        else:
            return render_template('login.html', error="اسم المستخدم أو كلمة المرور غير صحيحة")
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('main.home'))

# --- Nafath SSO ---

@auth_bp.route('/login/sso')
def login_sso():
    return get_nafath_redirect()

@auth_bp.route('/auth/callback')
def nafath_callback():
    token = oauth.nafath.authorize_access_token()
    user_info = oauth.nafath.get('userinfo').json() # Adjust based on actual Nafath response structure
    # For now, assume we get a national ID or CR linked to it
    # This is a placeholder for real Nafath logic
    return _handle_sso_login(user_info)

@auth_bp.route('/auth/callback/sim')
def nafath_callback_sim():
    # Simulated User Info
    user_info = {
        'national_id': '1010101010',
        'name_ar': 'مستخدم نفاد تجريبي',
        'name_en': 'Nafath Test User'
    }
    return _handle_sso_login(user_info)

def _handle_sso_login(user_info):
    # Logic to find or create user based on National ID
    # For prototype, we'll just log them in as a "Guest" or "Nafath User"
    # In production, you'd map National ID -> CR -> User
    
    session['user'] = {
        'id': 'nafath_' + user_info.get('national_id', '000'),
        'username': 'nafath_user',
        'name': user_info.get('name_ar', 'مسخدم نفاذ'),
        'name_en': user_info.get('name_en', 'Nafath User'),
        'cr': '1010084764', # Default to Almarai for demo purposes if no CR found
        'vat': '300084764000003',
        'type': 'business'
    }
    session.permanent = True
    return redirect(url_for('main.dashboard'))
