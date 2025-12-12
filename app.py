import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

from database import db
from models import User
from routes.auth import auth_bp
from routes.main import main_bp
from routes.contracts import contracts_bp
from services.email_service import mail
from services.nafath_service import init_nafath

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# App Factory
def create_app():
    app = Flask(__name__, static_folder='.', static_url_path='', template_folder='templates')
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///contracts.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    
    # Custom config for API KEY
    app.config['API_KEY'] = os.getenv('API_KEY', 'dev_api_key')

    # Security
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600

    # Extensions
    db.init_app(app)
    mail.init_app(app)
    init_nafath(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )

    # Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(contracts_bp)
    
    @app.route('/api/docs')
    def api_docs():
        return jsonify({
            'version': '1.0.0',
            'endpoints': {
                '/api/contract': 'POST - Create Contract',
                '/api/contract/<id>/sign': 'POST - Sign Contract',
                '/health': 'GET - System Health'
            }
        })
        
    return app

def seed_database(app):
    with app.app_context():
        db.create_all()
        # Check if users exist
        if User.query.first():
            return
            
        logger.info("Seeding database with mock data...")
        mock_users = [
            ('almarai', 'almarai123', 'شركة المراعي', 'Almarai Company', '1010084764', '300084764000003', '7000847640', 'الرياض', 'business'),
            ('stc', 'stc123', 'شركة الاتصالات السعودية', 'STC', '1010012345', '300012345600003', '7000012345', 'الرياض', 'business'),
            ('aramco', 'aramco123', 'أرامكو السعودية', 'Saudi Aramco', '2050008440', '300000844000003', '7000084400', 'الظهران', 'business'),
            ('sabic', 'sabic123', 'سابك', 'SABIC', '1010010030', '300010003000003', '7000100030', 'الرياض', 'business'),
            ('mobily', 'mobily123', 'شركة اتحاد اتصالات', 'Mobily', '1010209450', '300209450000003', '7002094500', 'الرياض', 'business'),
            ('zain', 'zain123', 'شركة زين السعودية', 'Zain KSA', '1010246713', '300246713000003', '7002467130', 'الرياض', 'business'),
            ('nahdi', 'nahdi123', 'شركة النهدي الطبية', 'Al Nahdi Medical', '4030073366', '300073366000003', '7000733660', 'جدة', 'business'),
            ('jarir', 'jarir123', 'مكتبة جرير', 'Jarir Bookstore', '1010043166', '300043166000003', '7000431660', 'الرياض', 'business'),
            ('extra', 'extra123', 'شركة اكسترا', 'Extra Stores', '1010230789', '300230789000003', '7002307890', 'الرياض', 'business'),
            ('demo', 'demo', 'شركة التقنية المتقدمة', 'Advanced Tech Co', '1010101010', '310101010100003', '7001010101', 'الرياض', 'business'),
        ]
        
        for u in mock_users:
            user = User(
                username=u[0],
                company_name=u[2],
                company_name_en=u[3],
                cr_number=u[4],
                vat_number=u[5],
                unified_number=u[6],
                city=u[7],
                user_type=u[8]
            )
            # Set password adds hash
            user.set_password(u[1])
            db.session.add(user)
        
        db.session.commit()
        logger.info("Database seeded.")

app = create_app()

if __name__ == '__main__':
    seed_database(app)
    port = int(os.getenv('SERVER_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
