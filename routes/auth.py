from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from models import User
from database import db

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
