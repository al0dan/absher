from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    company_name_en = db.Column(db.String(200))
    cr_number = db.Column(db.String(20))
    vat_number = db.Column(db.String(20))
    unified_number = db.Column(db.String(20))
    city = db.Column(db.String(100))
    user_type = db.Column(db.String(20), default='business')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Contract(db.Model):
    __tablename__ = 'contracts'

    id = db.Column(db.String(36), primary_key=True) # UUID
    supplier = db.Column(db.String(200), nullable=False)
    buyer = db.Column(db.String(200), nullable=False)
    supplier_vat = db.Column(db.String(20))
    buyer_vat = db.Column(db.String(20))
    supplier_cr = db.Column(db.String(20))
    buyer_cr = db.Column(db.String(20))
    items = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    contract_text = db.Column(db.Text)
    
    signed_by_supplier = db.Column(db.Boolean, default=False)
    signed_by_buyer = db.Column(db.Boolean, default=False)
    
    supplier_name = db.Column(db.String(200))
    buyer_name = db.Column(db.String(200))
    supplier_signature = db.Column(db.Text) # Base64 signature
    buyer_signature = db.Column(db.Text)   # Base64 signature
    
    supplier_token = db.Column(db.String(100), unique=True)
    buyer_token = db.Column(db.String(100), unique=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'supplier': self.supplier,
            'buyer': self.buyer,
            'items': self.items,
            'price': self.price,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': 'Complete' if (self.signed_by_supplier and self.signed_by_buyer) else 'Pending'
        }
