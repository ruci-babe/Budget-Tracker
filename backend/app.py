"""
Expense Tracker Sync Backend API
Enables syncing between desktop and mobile applications
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime, timedelta
import jwt

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///expense_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['JWT_EXPIRATION_HOURS'] = 24

db = SQLAlchemy(app)
CORS(app)

# ==================== Database Models ====================

class User(db.Model):
    """User account model for sync"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_sync = db.Column(db.DateTime)
    
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='user', lazy=True, cascade='all, delete-orphan')
    devices = db.relationship('Device', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_token(self):
        """Generate JWT token for authentication"""
        payload = {
            'user_id': self.id,
            'exp': datetime.utcnow() + timedelta(hours=app.config['JWT_EXPIRATION_HOURS'])
        }
        return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
        }


class Device(db.Model):
    """Track synced devices (desktop, mobile, web)"""
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    device_name = db.Column(db.String(120), nullable=False)
    device_type = db.Column(db.String(50), nullable=False)  # 'desktop', 'android', 'ios', 'web'
    device_id = db.Column(db.String(255), unique=True, nullable=False)  # UUID
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sync_logs = db.relationship('SyncLog', backref='device', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'device_id': self.device_id,
            'last_seen': self.last_seen.isoformat(),
            'created_at': self.created_at.isoformat(),
        }


class Category(db.Model):
    """User-defined expense categories"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(7), default='#2E86DE')  # hex color
    icon = db.Column(db.String(50))  # emoji or icon name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='category', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='unique_user_category'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'icon': self.icon,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class Transaction(db.Model):
    """Synced expense transactions"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    
    # Core transaction data
    date = db.Column(db.Date, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    vendor = db.Column(db.String(120))
    payment_method = db.Column(db.String(50))  # 'cash', 'card', 'mobile', 'email', 'imported'
    
    # Metadata
    is_recurring = db.Column(db.Boolean, default=False)
    is_duplicate = db.Column(db.Boolean, default=False)
    receipt_image = db.Column(db.String(255))  # URL/path to receipt image
    notes = db.Column(db.Text)
    
    # Sync tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = db.Column(db.DateTime)
    device_id = db.Column(db.String(255))  # Which device created/last modified
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'description': self.description,
            'amount': self.amount,
            'vendor': self.vendor,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'payment_method': self.payment_method,
            'is_recurring': self.is_recurring,
            'is_duplicate': self.is_duplicate,
            'receipt_image': self.receipt_image,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'synced_at': self.synced_at.isoformat() if self.synced_at else None,
        }


class SyncLog(db.Model):
    """Track sync operations for conflict resolution"""
    __tablename__ = 'sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False, index=True)
    sync_type = db.Column(db.String(50), nullable=False)  # 'pull', 'push', 'full'
    items_synced = db.Column(db.Integer, default=0)
    conflicts = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='success')  # 'success', 'partial', 'failed'
    error_message = db.Column(db.Text)
    synced_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sync_type': self.sync_type,
            'items_synced': self.items_synced,
            'conflicts': self.conflicts,
            'status': self.status,
            'error_message': self.error_message,
            'synced_at': self.synced_at.isoformat(),
        }


# ==================== Authentication Middleware ====================

def token_required(f):
    """Decorator to verify JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return {'message': 'Invalid authorization header'}, 401
        
        if not token:
            return {'message': 'Token is missing'}, 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return {'message': 'User not found'}, 401
        except jwt.ExpiredSignatureError:
            return {'message': 'Token has expired'}, 401
        except jwt.InvalidTokenError:
            return {'message': 'Invalid token'}, 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated


# ==================== API Routes ====================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'expense-tracker-sync'})


@app.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return {'message': 'Missing required fields'}, 400
    
    if User.query.filter_by(username=data['username']).first():
        return {'message': 'Username already exists'}, 409
    
    if User.query.filter_by(email=data['email']).first():
        return {'message': 'Email already exists'}, 409
    
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return {
        'message': 'User created successfully',
        'user': user.to_dict(),
        'token': user.generate_token()
    }, 201


@app.route('/auth/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return {'message': 'Missing username or password'}, 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return {'message': 'Invalid username or password'}, 401
    
    return {
        'message': 'Login successful',
        'user': user.to_dict(),
        'token': user.generate_token()
    }, 200


@app.route('/devices/register', methods=['POST'])
@token_required
def register_device(current_user):
    """Register a new device for syncing"""
    data = request.get_json()
    
    if not data or not data.get('device_name') or not data.get('device_type') or not data.get('device_id'):
        return {'message': 'Missing required fields'}, 400
    
    # Check if device already exists
    existing = Device.query.filter_by(device_id=data['device_id']).first()
    if existing:
        existing.last_seen = datetime.utcnow()
        db.session.commit()
        return {'message': 'Device already registered', 'device': existing.to_dict()}, 200
    
    device = Device(
        user_id=current_user.id,
        device_name=data['device_name'],
        device_type=data['device_type'],
        device_id=data['device_id']
    )
    
    db.session.add(device)
    db.session.commit()
    
    return {'message': 'Device registered', 'device': device.to_dict()}, 201


@app.route('/transactions/sync', methods=['POST'])
@token_required
def sync_transactions(current_user):
    """Sync transactions from mobile/desktop"""
    data = request.get_json()
    
    if not data:
        return {'message': 'No data provided'}, 400
    
    device_id = data.get('device_id')
    transactions = data.get('transactions', [])
    last_sync = data.get('last_sync')
    
    if not device_id:
        return {'message': 'device_id required'}, 400
    
    sync_log = SyncLog(device_id=0)  # Will be updated
    items_synced = 0
    conflicts = 0
    
    try:
        for tx_data in transactions:
            # Find or create transaction
            tx = Transaction.query.filter_by(
                user_id=current_user.id,
                date=tx_data['date'],
                description=tx_data['description'],
                amount=tx_data['amount']
            ).first()
            
            if not tx:
                tx = Transaction(user_id=current_user.id)
            else:
                conflicts += 1
            
            # Update transaction fields
            for key in ['date', 'description', 'amount', 'vendor', 'payment_method', 'notes']:
                if key in tx_data:
                    setattr(tx, key, tx_data[key])
            
            tx.synced_at = datetime.utcnow()
            tx.device_id = device_id
            db.session.add(tx)
            items_synced += 1
        
        db.session.commit()
        current_user.last_sync = datetime.utcnow()
        db.session.commit()
        
        return {
            'message': 'Sync successful',
            'items_synced': items_synced,
            'conflicts': conflicts,
            'server_timestamp': datetime.utcnow().isoformat()
        }, 200
    
    except Exception as e:
        db.session.rollback()
        return {'message': f'Sync failed: {str(e)}'}, 500


@app.route('/transactions', methods=['GET'])
@token_required
def get_transactions(current_user):
    """Get user's transactions (for mobile/desktop sync)"""
    since = request.args.get('since')
    limit = request.args.get('limit', 100, type=int)
    
    query = Transaction.query.filter_by(user_id=current_user.id)
    
    if since:
        try:
            since_date = datetime.fromisoformat(since)
            query = query.filter(Transaction.updated_at >= since_date)
        except ValueError:
            pass
    
    transactions = query.order_by(Transaction.date.desc()).limit(limit).all()
    
    return {
        'transactions': [tx.to_dict() for tx in transactions],
        'count': len(transactions),
        'server_timestamp': datetime.utcnow().isoformat()
    }, 200


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    return {'message': 'Endpoint not found'}, 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return {'message': 'Internal server error'}, 500


# ==================== Database Initialization ====================

def init_db():
    """Initialize database"""
    with app.app_context():
        db.create_all()
        print("Database initialized")


if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)
