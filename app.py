from datetime import datetime, timedelta
from flask import Flask, jsonify, request, redirect, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import random
import string
import os

# Load local .env (not committed) into the environment
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env_path):
    with open(_env_path, encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///banking_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-banking-2026')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
db = SQLAlchemy(app)

# Use Flask's built-in session (signed cookies)
import uuid

def create_session(user):
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    session['user_id'] = user.id
    session.permanent = True
    
    db_session = SessionToken(
        token=session_id,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=7)  # ✅ set explicitly
    )
    db.session.add(db_session)
    db.session.commit()
    return session_id

def destroy_session():
    """Destroy the backend session"""
    session_id = session.get('session_id')
    if session_id:
        db_session = SessionToken.query.filter_by(token=session_id).first()
        if db_session:
            db.session.delete(db_session)
            db.session.commit()
    session.clear()

def get_session_user():
    session_id = session.get('session_id')
    if not session_id:
        return None
    db_session = SessionToken.query.filter_by(token=session_id).first()
    if not db_session:
        return None
    print(f"[DEBUG] expires_at={db_session.expires_at}, now={datetime.utcnow()}")  # add this
    if db_session.expires_at < datetime.utcnow():
        return None
    return db_session.user

# ═══════════════════════════ EMAIL SERVICE ═══════════════════════════
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# SMTP configuration (from environment / .env)
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')

def send_email(to_email, subject, html_content):
    """Send HTML email matching website design"""
    if not SMTP_USER or not SMTP_PASS:
        # Log to console if SMTP not configured
        print(f"\n{'='*60}")
        print(f"📧 EMAIL (SMTP not configured - showing preview)")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"{'='*60}")
        print(html_content)
        print(f"{'='*60}\n")
        return True
    
    try:
        print(f"\n📧 SENDING EMAIL...")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f'GLOBALEASYTRANSASSET <{SMTP_USER}>'
        msg['To'] = to_email
        msg['Subject'] = subject
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def get_email_template(title, content, button_text=None, button_url=None, to_email=''):
    """Generate HTML email matching GLOBALEASYTRANSASSET website design"""
    button_html = ''
    if button_text and button_url:
        button_html = f'''
        <tr>
          <td style="padding: 30px 0;">
            <a href="{button_url}" style="background: linear-gradient(135deg, #1E6BFF 0%, #0B3D91 100%); color: #ffffff; padding: 16px 32px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 16px; display: inline-block;">{button_text}</a>
          </td>
        </tr>
        '''
    
    return f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f6f8fc;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background: #f6f8fc; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(30,107,255,0.10);">
          <!-- Header -->
          <tr>
            <td style="background: linear-gradient(160deg, #0B3D91 0%, #1E6BFF 60%, #0d52c2 100%); padding: 40px 40px 30px; text-align: center;">
              <div style="display: inline-flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                <div style="width: 44px; height: 44px; background: rgba(255,255,255,0.2); border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                  <span style="color: #fff; font-size: 22px; font-weight: 800;">G</span>
                </div>
                <span style="color: #ffffff; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">GLOBALEASYTRANSASSET</span>
              </div>
            </td>
          </tr>
          <!-- Content -->
          <tr>
            <td style="padding: 40px 40px 20px;">
              <h1 style="color: #0A0A0A; font-size: 28px; font-weight: 700; margin: 0 0 20px; text-align: center;">{title}</h1>
              <div style="color: #6B7280; font-size: 16px; line-height: 1.7; text-align: center;">
                {content}
              </div>
              {button_html}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background: #F6F8FC; padding: 30px 40px; text-align: center; border-top: 1px solid #E5EAF2;">
              <p style="color: #6B7280; font-size: 13px; margin: 0 0 10px;">
                GLOBALEASYTRANSASSET Financial Technologies Ltd
              </p>
              <p style="color: #9CA3AF; font-size: 12px; margin: 0;">
                This email was sent to {to_email}
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>'''

# ═══════════════════════════ EXCHANGE RATES ═══════════════════════════

EXCHANGE_API_BASE = 'https://api.exchangerate.host/latest'
EXCHANGE_BASE_CURRENCIES = ['USD', 'EUR', 'GBP']

RATES = {
    'USD': {'EUR': 0.92, 'GBP': 0.78},
    'EUR': {'USD': 1.09, 'GBP': 0.85},
    'GBP': {'USD': 1.28, 'EUR': 1.18},
}

CURRENCY_FLAGS = {'USD': '🇺🇸', 'EUR': '🇪🇺', 'GBP': '🇬🇧'}

# ═══════════════════════════ DATABASE MODELS ═══════════════════════════

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), default='')
    preferred_currency = db.Column(db.String(10), default='USD')
    status = db.Column(db.String(20), default='Active')
    is_admin = db.Column(db.Boolean, default=False)
    transaction_pin = db.Column(db.String(4), default='')  # 4-digit PIN for transactions
    account_number = db.Column(db.String(20), unique=True, index=True, nullable=False)  # Unique account number
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    accounts = db.relationship('Account', backref='user', lazy=True, cascade='all, delete-orphan')
    cards = db.relationship('VirtualCard', backref='user', lazy=True, cascade='all, delete-orphan')
    loans = db.relationship('Loan', backref='user', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    sessions = db.relationship('SessionToken', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': f'GA-{self.id:05d}',
            'accountNumber': self.account_number,
            'name': f"{self.first_name} {self.last_name}",
            'firstName': self.first_name,
            'lastName': self.last_name,
            'email': self.email,
            'username': self.username,
            'phone': self.phone,
            'preferredCurrency': self.preferred_currency,
            'status': self.status,
            'isAdmin': self.is_admin,
        }


class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        trends_data = {'USD': ('+1.2%', 'up'), 'EUR': ('+0.8%', 'up'), 'GBP': ('-0.3%', 'down')}
        trend, trend_state = trends_data.get(self.currency, ('—', 'neutral'))
        last4 = str(self.id).zfill(4)[-4:]
        return {
            'id': f"{self.currency.lower()}-{last4}",
            'currency': self.currency,
            'label': f"{self.currency} Account",
            'balance': self.balance,
            'flag': CURRENCY_FLAGS.get(self.currency, ''),
            'last4': last4,
            'trend': trend,
            'trendState': trend_state,
        }


class VirtualCard(db.Model):
    __tablename__ = 'virtual_cards'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    card_number = db.Column(db.String(20), unique=True)
    expiry = db.Column(db.String(10))
    balance = db.Column(db.Float, default=0.0)
    card_limit = db.Column(db.Float, default=5000.0)
    status = db.Column(db.String(20), default='active')
    theme = db.Column(db.String(20), default='dark')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, user):
        return {
            'id': f"card-{self.id}",
            'last4': self.card_number[-4:] if self.card_number else '0000',
            'holder_name': f"{user.first_name} {user.last_name}",
            'expiry': self.expiry or '12/28',
            'status': self.status,
            'balance': self.balance,
            'limit': self.card_limit,
            'spent': self.card_limit - self.balance if self.balance else 0,
            'plan': 'Standard' if self.card_limit <= 5000 else 'Premium' if self.card_limit <= 25000 else 'Elite',
            'design': self.theme or 'dark',
            'network': 'VIRTUAL',
        }


class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    loan_type = db.Column(db.String(100))
    original_amount = db.Column(db.Float)
    balance = db.Column(db.Float)
    monthly_payment = db.Column(db.Float)
    interest_rate = db.Column(db.Float)
    term_months = db.Column(db.Integer)
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        progress = max(0, min(100, int(((self.original_amount - self.balance) / self.original_amount * 100) if self.original_amount else 0)))
        return {
            'id': f"loan-{self.id}",
            'type': self.loan_type,
            'original': self.original_amount,
            'balance': self.balance,
            'monthly': self.monthly_payment,
            'interest': self.interest_rate,
            'term': f"{self.term_months} months",
            'progress': progress,
            'status': self.status,
        }


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    tx_type = db.Column(db.String(100))
    date = db.Column(db.String(20))
    category = db.Column(db.String(50))
    amount = db.Column(db.Float)
    currency = db.Column(db.String(10), default='USD')
    direction = db.Column(db.String(10))
    status = db.Column(db.String(20), default='Completed')
    details = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.reference,
            'type': self.tx_type,
            'date': self.date,
            'category': self.category,
            'amount': self.amount,
            'currency': self.currency,
            'direction': self.direction,
            'status': self.status,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SessionToken(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # ❌ OLD - lambda may not work reliably as column default
    # expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    
    # ✅ FIX - set it explicitly in create_session instead
    expires_at = db.Column(db.DateTime, nullable=False)

class VerificationOTP(db.Model):
    __tablename__ = 'verification_otps'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))
    verified = db.Column(db.Boolean, default=False)


# ═══════════════════════════ HELPER FUNCTIONS ═══════════════════════════

def make_token(length=40):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def get_auth_token():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ', 1)[1].strip()
    data = request.get_json(silent=True) or {}
    token = data.get('token') or request.args.get('token')
    print(f"[AUTH] get_auth_token: token={token[:20] if token else 'None'}...")
    return token


def current_user():
    token = get_auth_token()
    if not token:
        print("[AUTH] current_user: no token")
        return None
    session = SessionToken.query.filter_by(token=token).first()
    if not session:
        print(f"[AUTH] current_user: session not found for token {token[:20]}...")
        return None
    if session.expires_at <= datetime.utcnow():
        print(f"[AUTH] current_user: session expired")
        return None
    print(f"[AUTH] current_user: found user {session.user.email}")
    return session.user


def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_session_user()
        if not user:
            return jsonify(success=False, error='Authentication required'), 401
        return fn(user, *args, **kwargs)
    return wrapper


def fetch_live_rates():
    """Fetch latest USD/EUR/GBP exchange rates from exchangerate.host and hydrate the local rate table."""
    try:
        from urllib.request import Request, urlopen
        import json

        symbols = ','.join([c for c in EXCHANGE_BASE_CURRENCIES if c != 'USD'])
        url = f"{EXCHANGE_API_BASE}?base=USD&symbols={symbols}"
        request_obj = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(request_obj, timeout=5) as response:
            payload = json.loads(response.read().decode('utf-8'))

        if not payload.get('success', True) or 'rates' not in payload:
            return False

        usd_rates = payload['rates']
        eur = usd_rates.get('EUR')
        gbp = usd_rates.get('GBP')
        if not eur or not gbp:
            return False

        RATES['USD']['EUR'] = eur
        RATES['USD']['GBP'] = gbp
        RATES['EUR']['USD'] = 1.0 / eur
        RATES['GBP']['USD'] = 1.0 / gbp
        RATES['EUR']['GBP'] = gbp / eur
        RATES['GBP']['EUR'] = eur / gbp
        return True
    except Exception:
        return False


def generate_card_number():
    return f"{random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}"


def generate_expiry():
    expiry = datetime.now() + timedelta(days=365*3)
    return f"{expiry.month:02d}/{expiry.year % 100:02d}"


def generate_tx_ref():
    return f"GA-TXN-{random.randint(10000000, 99999999)}"


def seed_demo_data(user):
    if user.accounts:
        return
    
    accounts = [
        Account(user_id=user.id, currency='USD', balance=random.uniform(100000, 200000)),
        Account(user_id=user.id, currency='EUR', balance=random.uniform(50000, 100000)),
        Account(user_id=user.id, currency='GBP', balance=random.uniform(30000, 80000)),
    ]
    
    cards = [
        VirtualCard(user_id=user.id, card_number=generate_card_number(), expiry=generate_expiry(), balance=2000.00, card_limit=5000.00, status='active', theme='dark'),
        VirtualCard(user_id=user.id, card_number=generate_card_number(), expiry=generate_expiry(), balance=1050.00, card_limit=3000.00, status='active', theme='midnight'),
    ]
    
    loans = [
        Loan(user_id=user.id, loan_type='Personal Loan', original_amount=20000.00, balance=11400.00, monthly_payment=950.00, interest_rate=6.2, term_months=24, status='On track'),
        Loan(user_id=user.id, loan_type='Mortgage', original_amount=425000.00, balance=328500.00, monthly_payment=2200.00, interest_rate=4.15, term_months=360, status='Steady'),
    ]
    
    now = datetime.utcnow()
    transactions = [
        Transaction(user_id=user.id, reference='txn-1001', tx_type='Salary deposit', date='Apr 15', category='Income', amount=6200.00, currency='USD', direction='in', status='Completed', details='Monthly salary', created_at=now - timedelta(days=1, hours=3)),
        Transaction(user_id=user.id, reference='txn-1002', tx_type='Wire transfer', date='Apr 14', category='Transfer', amount=12750.00, currency='USD', direction='out', status='Completed', details='Payment to recipient', created_at=now - timedelta(days=2, hours=4)),
        Transaction(user_id=user.id, reference='txn-1003', tx_type='Card payment', date='Apr 13', category='Card', amount=890.00, currency='USD', direction='out', status='Completed', details='Cloud services', created_at=now - timedelta(days=3, hours=5)),
        Transaction(user_id=user.id, reference='txn-1004', tx_type='Utility bill', date='Apr 13', category='Bills', amount=198.45, currency='USD', direction='out', status='Completed', details='Electricity payment', created_at=now - timedelta(days=4, hours=2)),
        Transaction(user_id=user.id, reference='txn-1005', tx_type='Grocery market', date='Apr 11', category='Food', amount=156.20, currency='USD', direction='out', status='Completed', details='Groceries', created_at=now - timedelta(days=5, hours=6)),
    ]
    
    db.session.add_all(accounts + cards + loans + transactions)
    db.session.commit()


# ═══════════════════════════ ROUTES ═══════════════════════════

@app.after_request
def add_no_cache_headers(response):
    """Prevent browser caching for all HTML pages"""
    if request.path.endswith('.html'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/')
def root():
    return redirect('/home')


# HTML pages without .html extension
@app.route('/home')
def home():
    return send_from_directory('.', 'home.html')

@app.route('/login')
def login():
    return send_from_directory('.', 'login.html')

@app.route('/register')
def register():
    return send_from_directory('.', 'register.html')

@app.route('/Signup')
def signup():
    return send_from_directory('.', 'Signup.html')

@app.route('/dashboard')
def dashboard():
    return send_from_directory('.', 'dashboard.html')

@app.route('/virtual-card')
def virtual_card():
    return send_from_directory('.', 'virtual-card.html')

@app.route('/wire-transfer')
def wire_transfer():
    return send_from_directory('.', 'wire-transfer.html')

@app.route('/transaction-history')
def transaction_history():
    return send_from_directory('.', 'transaction-history.html')

@app.route('/loan-mortgage')
def loan_mortgage():
    return send_from_directory('.', 'loan-mortgage.html')

@app.route('/settings')
def settings():
    return send_from_directory('.', 'settings.html')

@app.route('/help-support')
def help_support():
    return send_from_directory('.', 'help-support.html')

@app.route('/admin')
def admin():
    return send_from_directory('.', 'admin.html')


@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)


ADMIN_LOGIN_EMAIL = os.environ.get('ADMIN_LOGIN_EMAIL', 'globaleasytransasset')
ADMIN_LOGIN_PASSWORD = os.environ.get('ADMIN_LOGIN_PASSWORD', '')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify(success=False, error='Invalid email or password'), 401

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        # Check for admin credentials
        if ADMIN_LOGIN_PASSWORD and email == ADMIN_LOGIN_EMAIL and password == ADMIN_LOGIN_PASSWORD:
            # Create or get admin user
            admin_user = User.query.filter_by(email='globaleasytransasset@admin.com').first()
            if not admin_user:
                admin_user = User(
                    email='globaleasytransasset@admin.com',
                    username='admin',
                    first_name='Admin',
                    last_name='Global',
                    is_admin=True,
                    is_verified=True,
                    kyc_status='approved'
                )
                admin_user.set_password(ADMIN_LOGIN_PASSWORD)
                db.session.add(admin_user)
                db.session.commit()
            create_session(admin_user)
            return jsonify(success=True, user=admin_user.to_dict()), 200
        return jsonify(success=False, error='Invalid email or password'), 401

    # Create backend session (no token needed - uses cookies)
    create_session(user)

    return jsonify(success=True, user=user.to_dict()), 200


@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    first_name = data.get('firstName', 'New').strip()
    last_name = data.get('lastName', 'User').strip()
    username = data.get('username', email.split('@')[0] if email else '').strip()
    phone = data.get('phone', '').strip()

    if not email or '@' not in email:
        return jsonify(success=False, error='Please provide a valid email.'), 400
    if not password or len(password) < 6:
        return jsonify(success=False, error='Password must be at least 6 characters.'), 400
    if User.query.filter_by(email=email).first():
        return jsonify(success=False, error='Account already exists with that email.'), 409

    # Generate OTP for email verification
    otp_code = ''.join(random.choices(string.digits, k=6))
    
    # Store OTP in database
    otp_record = VerificationOTP(email=email, otp_code=otp_code)
    db.session.add(otp_record)
    db.session.commit()

    # Send OTP email with styled template
    otp_html = get_email_template(
        title='Verify Your Email',
        content=f'''
          <p style="margin-bottom: 20px;">Thanks for signing up with GLOBALEASYTRANSASSET!</p>
          <p style="margin-bottom: 10px;">Your verification code is:</p>
          <div style="background: #EBF2FF; padding: 20px; border-radius: 12px; display: inline-block; margin: 20px 0;">
            <span style="font-size: 32px; font-weight: 700; color: #1E6BFF; letter-spacing: 8px;">{otp_code}</span>
          </div>
          <p style="color: #6B7280; font-size: 14px;">This code expires in 10 minutes.</p>
          <p style="color: #9CA3AF; font-size: 13px; margin-top: 20px;">If you didn't create an account, you can safely ignore this email.</p>
        '''
    )
    send_email(
        to_email=email,
        subject='Verify your GLOBALEASYTRANSASSET account',
        html_content=otp_html
    )

    # Return success - frontend should show OTP screen
    return jsonify(success=True, email=email, message='Verification code sent to your email'), 201


@app.route('/api/verify-otp', methods=['POST'])
def api_verify_otp():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    otp_code = data.get('otp', '').strip()

    if not email or not otp_code:
        return jsonify(success=False, error='Email and OTP code required.'), 400

    # Find the most recent unverified OTP for this email
    otp_record = VerificationOTP.query.filter_by(
        email=email, 
        otp_code=otp_code, 
        verified=False
    ).order_by(VerificationOTP.created_at.desc()).first()

    if not otp_record:
        return jsonify(success=False, error='Invalid verification code.'), 400

    if otp_record.expires_at < datetime.utcnow():
        return jsonify(success=False, error='Verification code has expired.'), 400

    # Mark OTP as verified
    otp_record.verified = True
    db.session.commit()

    # Get the registration data from the request
    password = data.get('password', '')
    first_name = data.get('firstName', 'New').strip()
    last_name = data.get('lastName', 'User').strip()
    phone = data.get('phone', '').strip()
    username = email.split('@')[0] if email else ''

    # Generate unique numeric account number
    while True:
        acc_num = ''.join([str(random.randint(1, 9))] + random.choices(string.digits, k=9))
        if not User.query.filter_by(account_number=acc_num).first():
            break

    # Create the user
    user = User(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        preferred_currency='USD',
        status='Active',
        account_number=acc_num
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Create backend session (no token needed - uses cookies)
    create_session(user)

    # Send welcome email with styled template
    welcome_html = get_email_template(
        title='Welcome to GLOBALEASYTRANSASSET!',
        content=f'''
          <p style="margin-bottom: 20px;">Hello {first_name},</p>
          <p style="margin-bottom: 20px;">Welcome to GLOBALEASYTRANSASSET! Your account has been successfully created.</p>
          <div style="background: #F6F8FC; padding: 24px; border-radius: 12px; text-align: left; margin: 20px 0;">
            <p style="margin: 0 0 10px; color: #6B7280; font-size: 14px;"><strong style="color: #0A0A0A;">Email:</strong> {email}</p>
            <p style="margin: 0 0 10px; color: #6B7280; font-size: 14px;"><strong style="color: #0A0A0A;">Username:</strong> {username}</p>
            <p style="margin: 0; color: #6B7280; font-size: 14px;"><strong style="color: #0A0A0A;">Account Number:</strong> {acc_num}</p>
          </div>
          <p style="color: #6B7280; font-size: 14px;">You can now log in and start using our banking services.</p>
        ''',
        button_text='Go to Dashboard',
        button_url='http://127.0.0.1:5000/dashboard'
    )
    send_email(
        to_email=email,
        subject='Welcome to GLOBALEASYTRANSASSET!',
        html_content=welcome_html
    )

    return jsonify(success=True, user=user.to_dict()), 201


@app.route('/api/dashboard')
@auth_required
def api_dashboard(user):
    total_balance = sum(a.balance for a in user.accounts)
    money_in = sum(t.amount for t in user.transactions if t.direction == 'in')
    money_out = sum(t.amount for t in user.transactions if t.direction == 'out')

    return jsonify(
        success=True,
        user=user.to_dict(),
        stats={
            'totalBalance': total_balance,
            'moneyReceived': money_in,
            'moneySent': money_out,
            'savingsBalance': sum(a.balance for a in user.accounts if a.currency == 'USD'),
            'virtualCards': len(user.cards),
        },
        accounts=[a.to_dict() for a in user.accounts],
        recentTransactions=[t.to_dict() for t in sorted(user.transactions, key=lambda x: x.created_at, reverse=True)[:5]],
        cards=[c.to_dict(user) for c in user.cards],
        loans=[l.to_dict() for l in user.loans],
    ), 200


COUNTRIES = [
    'Afghanistan','Albania','Algeria','Andorra','Angola','Antigua and Barbuda',
    'Argentina','Armenia','Australia','Austria','Azerbaijan','Bahamas','Bahrain',
    'Bangladesh','Barbados','Belarus','Belgium','Belize','Benin','Bhutan',
    'Bolivia','Bosnia and Herzegovina','Botswana','Brazil','Brunei','Bulgaria',
    'Burkina Faso','Burundi','Cambodia','Cameroon','Canada','Cape Verde',
    'Central African Republic','Chad','Chile','China','Colombia','Comoros',
    'Congo','Costa Rica','Croatia','Cuba','Cyprus','Czech Republic','Denmark',
    'Djibouti','Dominica','Dominican Republic','Ecuador','Egypt','El Salvador',
    'Equatorial Guinea','Eritrea','Estonia','Ethiopia','Fiji','Finland','France',
    'Gabon','Gambia','Georgia','Germany','Ghana','Greece','Grenada','Guatemala',
    'Guinea','Guinea-Bissau','Guyana','Haiti','Honduras','Hungary','Iceland',
    'India','Indonesia','Iran','Iraq','Ireland','Israel','Italy','Jamaica',
    'Japan','Jordan','Kazakhstan','Kenya','Kiribati','Kuwait','Kyrgyzstan',
    'Laos','Latvia','Lebanon','Lesotho','Liberia','Libya','Liechtenstein',
    'Lithuania','Luxembourg','Madagascar','Malawi','Malaysia','Maldives','Mali',
    'Malta','Marshall Islands','Mauritania','Mauritius','Mexico','Micronesia',
    'Moldova','Monaco','Mongolia','Montenegro','Morocco','Mozambique','Myanmar',
    'Namibia','Nauru','Nepal','Netherlands','New Zealand','Nicaragua','Niger',
    'Nigeria','North Korea','North Macedonia','Norway','Oman','Pakistan',
    'Palau','Palestine','Panama','Papua New Guinea','Paraguay','Peru',
    'Philippines','Poland','Portugal','Qatar','Romania','Russia','Rwanda',
    'Saint Kitts and Nevis','Saint Lucia','Saint Vincent and the Grenadines',
    'Samoa','San Marino','Sao Tome and Principe','Saudi Arabia','Senegal',
    'Serbia','Seychelles','Sierra Leone','Singapore','Slovakia','Slovenia',
    'Solomon Islands','Somalia','South Africa','South Korea','South Sudan',
    'Spain','Sri Lanka','Sudan','Suriname','Sweden','Switzerland','Syria',
    'Taiwan','Tajikistan','Tanzania','Thailand','Timor-Leste','Togo','Tonga',
    'Trinidad and Tobago','Tunisia','Turkey','Turkmenistan','Tuvalu','Uganda',
    'Ukraine','United Arab Emirates','United Kingdom','United States','Uruguay',
    'Uzbekistan','Vanuatu','Vatican City','Venezuela','Vietnam','Yemen',
    'Zambia','Zimbabwe','Other'
]

@app.route('/api/wire-transfer/options')
@auth_required
def api_wire_options(user):
    fetch_live_rates()
    active_card = VirtualCard.query.filter_by(user_id=user.id, status='active').first()
    if not active_card:
        return jsonify(success=False, error='You need an active virtual card to perform wire transfers.'), 403

    # Calculate used amounts this month/day
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    monthly_used = sum(t.amount for t in user.transactions 
                      if t.created_at >= month_start and t.direction == 'out')
    daily_used = sum(t.amount for t in user.transactions 
                    if t.created_at >= day_start and t.direction == 'out')
    daily_count = sum(1 for t in user.transactions 
                      if t.created_at >= day_start and t.direction == 'out' and t.category == 'Transfer')
    monthly_count = sum(1 for t in user.transactions 
                        if t.created_at >= month_start and t.direction == 'out' and t.category == 'Transfer')
    
    return jsonify(
        success=True,
        accounts=[a.to_dict() for a in user.accounts],
        currencies=list(RATES.keys()),
        rates=RATES,
        countries=COUNTRIES,
        paymentMethods=['Bank Transfer', 'Mobile Money', 'Digital Wallet'],
        recentTransfers=[t.to_dict() for t in sorted(user.transactions, key=lambda x: x.created_at, reverse=True) if t.category == 'Transfer'][:4],
        limits={
            'daily': {'used': daily_used, 'limit': 1000000000, 'remaining': max(0, 1000000000 - daily_used), 'count': daily_count, 'countLimit': 10, 'countRemaining': max(0, 10 - daily_count)},
            'monthly': {'used': monthly_used, 'limit': 1000000000, 'remaining': max(0, 1000000000 - monthly_used), 'count': monthly_count, 'countLimit': 50, 'countRemaining': max(0, 50 - monthly_count)},
            'perTransaction': 1000000000,
            'minTransaction': 100
        }
    ), 200


@app.route('/api/wire-transfer', methods=['POST'])
@auth_required
def api_wire_transfer(user):
    fetch_live_rates()
    data = request.get_json(silent=True) or {}
    from_currency = data.get('fromCurrency')
    to_currency = data.get('toCurrency')
    amount = float(data.get('amount') or 0)
    note = data.get('note', '')
    payment_method = data.get('paymentMethod', 'bank')
    gateway_url = data.get('cryptoWallet', '')

    if not from_currency or not to_currency or amount <= 0:
        return jsonify(success=False, error='Invalid transfer details'), 400

    active_card = VirtualCard.query.filter_by(user_id=user.id, status='active').first()
    if not active_card:
        return jsonify(success=False, error='Wire transfers require an active virtual card. Please add one before sending funds.'), 403

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    daily_count = sum(1 for t in user.transactions 
                      if t.created_at >= day_start and t.direction == 'out' and t.category == 'Transfer')
    monthly_count = sum(1 for t in user.transactions 
                        if t.created_at >= month_start and t.direction == 'out' and t.category == 'Transfer')
    daily_used = sum(t.amount for t in user.transactions 
                    if t.created_at >= day_start and t.direction == 'out')
    monthly_used = sum(t.amount for t in user.transactions 
                      if t.created_at >= month_start and t.direction == 'out')

    min_amount = 100
    max_per_transaction = 1000000000
    daily_max_amount = 1000000000
    monthly_max_amount = 1000000000
    daily_max_count = 10
    monthly_max_count = 50

    if amount < min_amount:
        return jsonify(success=False, error=f'Minimum wire transfer amount is ${min_amount:,}'), 400
    if amount > max_per_transaction:
        return jsonify(success=False, error=f'Maximum transfer per transaction is ${max_per_transaction:,}'), 400
    if daily_count >= daily_max_count:
        return jsonify(success=False, error='Daily wire transfer count limit reached'), 400
    if monthly_count >= monthly_max_count:
        return jsonify(success=False, error='Monthly wire transfer count limit reached'), 400
    if amount > daily_max_amount - daily_used:
        return jsonify(success=False, error='Requested amount exceeds your daily transfer amount limit'), 400
    if amount > monthly_max_amount - monthly_used:
        return jsonify(success=False, error='Requested amount exceeds your monthly transfer amount limit'), 400

    from_acct = Account.query.filter_by(user_id=user.id, currency=from_currency).first()
    if not from_acct or from_acct.balance < amount:
        return jsonify(success=False, error='Insufficient funds'), 400

    rate = RATES.get(from_currency, {}).get(to_currency, 1.0)
    received = round(amount * rate, 2)
    ref = generate_tx_ref()

    from_acct.balance -= amount
    
    # Build details based on payment method
    details = f'Amount: {amount} {from_currency}'
    if payment_method == 'crypto' and gateway_url:
        details += f' | Gateway URL provided'
    if note:
        details += f' | {note}'
    
    txn = Transaction(
        user_id=user.id,
        reference=ref,
        tx_type=f'Wire Transfer',
        date=datetime.now().strftime('%b %d'),
        category='Transfer',
        amount=amount,
        currency=from_currency,
        direction='out',
        status='pending',  # Set to pending for admin approval
        details=details
    )
    db.session.add(txn)
    db.session.commit()

    return jsonify(
        success=True,
        reference=ref,
        fromCurrency=from_currency,
        toCurrency=to_currency,
        amount=amount,
        receivedAmount=received,
        rate=rate,
        eta='1-2 business days',
        paymentMethod=payment_method,
    ), 200


@app.route('/api/virtual-card')
@auth_required
def api_virtual_card(user):
    # Get current crypto rates (in production, fetch from real API)
    rates = {
        'BTC': 0.029,  # ~$2,000 at ~$69k BTC
        'USDT-ERC20': 2000.00,
        'USDT-TRC20': 2000.00
    }
    
    # Wallet addresses for payments
    wallets = {
        'BTC': 'bc1qzrmz7h0ylud5mczmwq5aaz3mf2vhwh8djwm7j5',
        'USDT-ERC20': '0x24dd6382A03a42B2dEEf8C3A13A27a790b1Fbf14',
        'USDT-TRC20': 'TTUZFPKm25qGcHXEQWVNMEnJsMdX6RprWG'
    }
    
    return jsonify(
        success=True,
        cards=[c.to_dict(user) for c in user.cards],
        rates=rates,
        wallets=wallets,
        planName='Standard',
        userName=f"{user.first_name} {user.last_name}",
    ), 200


@app.route('/api/virtual-card/purchase', methods=['POST'])
@auth_required
def api_virtual_card_purchase(user):
    data = request.json
    design = data.get('design', 'Standard')
    plan = data.get('plan', 'Standard')
    crypto = data.get('crypto', 'btc')
    amount = float(data.get('amount', 2))
    
    # Determine card limit based on plan
    limits = {'Standard': 5000, 'Premium': 25000, 'Elite': 100000}
    card_limit = limits.get(plan, 5000)
    
    # Generate card number (16 digits)
    card_number = ''.join([str(random.randint(0, 9)) for _ in range(16)])
    
    # Generate expiry (2 years from now)
    expiry = f"{random.randint(1,12):02d}/{datetime.now().year + 2}"
    
    # Create new card
    new_card = VirtualCard(
        user_id=user.id,
        card_number=card_number,
        expiry=expiry,
        balance=0.0,
        card_limit=card_limit,
        status='pending',  # Set to pending for admin approval
        theme=design.lower()
    )
    db.session.add(new_card)
    db.session.commit()
    
    # Create transaction record
    txn = Transaction(
        user_id=user.id,
        reference=generate_tx_ref(),
        tx_type='Card Purchase',
        date=datetime.now().strftime('%b %d'),
        category='Card',
        amount=amount,
        currency=crypto.upper() if crypto else 'USD',
        direction='out',
        status='pending',  # Set to pending for admin approval
        details=f"Virtual Card ({design} - {plan})"
    )
    db.session.add(txn)
    db.session.commit()
    
    return jsonify(
        success=True,
        message=f"Virtual card created successfully!",
        card=new_card.to_dict(user)
    ), 200


@app.route('/api/virtual-card/freeze', methods=['POST'])
@auth_required
def api_virtual_card_freeze(user):
    data = request.json
    card_id = data.get('cardId', '').replace('card-', '')
    
    try:
        card = VirtualCard.query.filter_by(id=int(card_id), user_id=user.id).first()
        if not card:
            return jsonify(success=False, message='Card not found'), 404
        
        # Toggle status
        if card.status == 'active':
            card.status = 'frozen'
            message = 'Card frozen successfully'
        else:
            card.status = 'active'
            message = 'Card unfrozen successfully'
        
        db.session.commit()
        return jsonify(success=True, message=message, card=card.to_dict(user)), 200
    except Exception as e:
        return jsonify(success=False, message=str(e)), 400


@app.route('/api/loans')
@auth_required
def api_loans(user):
    return jsonify(success=True, loans=[l.to_dict() for l in user.loans]), 200


@app.route('/api/transactions')
@auth_required
def api_transactions(user):
    txns = sorted(user.transactions, key=lambda t: t.created_at, reverse=True)
    money_in = sum(t.amount for t in txns if t.direction == 'in')
    money_out = sum(t.amount for t in txns if t.direction == 'out')
    
    return jsonify(
        success=True,
        transactions=[t.to_dict() for t in txns],
        summary={
            'last30Days': money_in - money_out,
            'averageDaily': (money_in - money_out) / 30 if txns else 0,
            'balances': {
                'Checking': sum(a.balance for a in user.accounts if a.currency == 'USD'),
                'Savings': sum(a.balance for a in user.accounts if a.currency == 'EUR'),
                'Pending': 0,
            },
        },
    ), 200

@app.route('/api/loans', methods=['GET'])
@auth_required
def api_loans_list(user):
    return jsonify(
        success=True,
        loans=[l.to_dict() for l in user.loans]
    ), 200


@app.route('/api/loan-mortgage', methods=['POST'])
@auth_required
def loan_mortgage_api(user):
    data = request.json
    loan_type = data.get('type', 'Personal Loan')
    amount = float(data.get('amount', 0))
    term = int(data.get('duration', 24))
    
    # Calculate loan details
    interest_rate = 6.2  # Example rate
    monthly_rate = interest_rate / 100 / 12
    monthly_payment = (amount * monthly_rate * (1 + monthly_rate) ** term) / ((1 + monthly_rate) ** term - 1) if monthly_rate > 0 else amount / term
    
    # Create new loan
    new_loan = Loan(
        user_id=user.id,
        loan_type=loan_type,
        original_amount=amount,
        balance=amount,
        monthly_payment=monthly_payment,
        interest_rate=interest_rate,
        term_months=term,
        status='Active'
    )
    db.session.add(new_loan)
    db.session.commit()
    
    return jsonify({
        "success": True, 
        "message": f"Loan application submitted! Your {loan_type} of ${amount:,.2f} has been approved.",
        "loan": new_loan.to_dict()
    })

@app.route('/api/settings', methods=['GET', 'POST'])
@auth_required
def api_settings(user):
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        user.first_name = data.get('firstName', user.first_name)
        user.last_name = data.get('lastName', user.last_name)
        user.phone = data.get('phone', user.phone)
        user.preferred_currency = data.get('preferredCurrency', user.preferred_currency)
        user.updated_at = datetime.utcnow()
        db.session.commit()
    
    return jsonify(success=True, settings=user.to_dict()), 200


@app.route('/api/transaction-pin', methods=['GET', 'POST'])
@auth_required
def api_transaction_pin(user):
    """Get or set transaction PIN"""
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        pin = data.get('pin', '')
        
        # Validate PIN is 4 digits
        if not pin or len(pin) != 4 or not pin.isdigit():
            return jsonify(success=False, error='PIN must be 4 digits'), 400
        
        user.transaction_pin = pin
        db.session.commit()
        return jsonify(success=True, message='PIN set successfully'), 200
    
    # GET - return whether PIN is set
    return jsonify(success=True, hasPin=bool(user.transaction_pin)), 200


@app.route('/api/verify-pin', methods=['POST'])
@auth_required
def api_verify_pin(user):
    """Verify transaction PIN"""
    data = request.get_json(silent=True) or {}
    pin = data.get('pin', '')
    
    if not user.transaction_pin:
        return jsonify(success=False, error='No PIN set'), 400
    
    if pin == user.transaction_pin:
        return jsonify(success=True), 200
    
    return jsonify(success=False, error='Invalid PIN'), 401


@app.route('/api/support', methods=['GET'])
@auth_required
def api_support(user):
    return jsonify(
        success=True,
        support={
            'contacts': [
                {'mode': 'Chat', 'label': 'Live chat with support', 'action': 'chat'},
                {'mode': 'Email', 'label': 'Send a support message', 'action': 'email'},
                {'mode': 'Call', 'label': 'Request a callback', 'action': 'call'},
            ],
            'resources': [
                {'title': 'How do I update my transfer limit?', 'description': 'Visit account settings to adjust daily payment limits or contact support.'},
                {'title': 'What should I do if my account is locked?', 'description': 'Use our secure verification flow to restore access.'},
                {'title': 'Where can I view dispute status?', 'description': 'Transaction disputes are tracked in the transaction history view.'},
            ],
        },
    ), 200

# ═══════════════════════════ STANDALONE ADMIN AUTH ═══════════════════════════

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'globaleasytransassets')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    
    if ADMIN_PASSWORD and username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['is_admin'] = True
        session.permanent = True
        return jsonify(success=True), 200
    
    return jsonify(success=False, error='Invalid credentials'), 401

@app.route('/api/admin/logout', methods=['POST'])
def api_admin_logout():
    session.pop('is_admin', None)
    return jsonify(success=True), 200

@app.route('/api/admin/check', methods=['GET'])
def api_admin_check():
    if session.get('is_admin'):
        return jsonify(success=True), 200
    return jsonify(success=False), 401
@app.route('/api/health')
def api_health():
    return jsonify(success=True, status='online', timestamp=datetime.utcnow().isoformat()), 200


@app.route('/api/check-auth')
def api_check_auth():
    """Check if user is logged in via backend session"""
    user = get_session_user()
    if user:
        return jsonify(success=True, user=user.to_dict()), 200
    return jsonify(success=False, error='Not logged in'), 401


@app.route('/api/logout')
def api_logout():
    """Logout and destroy backend session"""
    destroy_session()
    return jsonify(success=True), 200


@app.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    """Request password reset - send OTP to user's email"""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    
    if not email or '@' not in email:
        return jsonify(success=False, error='Please provide a valid email address.'), 400
    
    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        # Don't reveal if user exists or not for security
        return jsonify(success=True, message='If an account exists, a reset link has been sent.'), 200
    
    # Generate OTP for password reset
    reset_otp = ''.join(random.choices(string.digits, k=6))
    
    # Store OTP in database (reuse VerificationOTP table or create new)
    otp_record = VerificationOTP(
        email=email,
        otp_code=reset_otp,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=15),
        verified=False
    )
    db.session.add(otp_record)
    db.session.commit()
    
    # Send reset email
    reset_html = get_email_template(
        title='Reset Your Password',
        content=f'''
          <p style="margin-bottom: 20px;">We received a request to reset your GLOBALEASYTRANSASSET password.</p>
          <p style="margin-bottom: 10px;">Your reset code is:</p>
          <div style="background: #EBF2FF; padding: 20px; border-radius: 12px; display: inline-block; margin: 20px 0;">
            <span style="font-size: 32px; font-weight: 700; color: #1E6BFF; letter-spacing: 8px;">{reset_otp}</span>
          </div>
          <p style="color: #6B7280; font-size: 14px;">This code expires in 15 minutes.</p>
          <p style="color: #9CA3AF; font-size: 13px; margin-top: 20px;">If you didn't request a password reset, you can safely ignore this email.</p>
        ''',
        button_text='Go to Login',
        button_url='http://127.0.0.1:5000/login'
    )
    send_email(
        to_email=email,
        subject='Reset your GLOBALEASYTRANSASSET password',
        html_content=reset_html
    )
    
    return jsonify(success=True, message='If an account exists, a reset link has been sent.'), 200


@app.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    """Reset password using OTP"""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    otp_code = data.get('otp', '').strip()
    new_password = data.get('newPassword', '')
    
    if not email or '@' not in email:
        return jsonify(success=False, error='Email is required.'), 400
    if not otp_code or len(otp_code) != 6:
        return jsonify(success=False, error='Invalid OTP code.'), 400
    if not new_password or len(new_password) < 6:
        return jsonify(success=False, error='Password must be at least 6 characters.'), 400
    
    # Find the most recent unverified OTP for this email
    otp_record = VerificationOTP.query.filter_by(
        email=email, 
        otp_code=otp_code, 
        verified=False
    ).order_by(VerificationOTP.created_at.desc()).first()
    
    if not otp_record:
        return jsonify(success=False, error='Invalid verification code.'), 400
    
    if otp_record.expires_at < datetime.utcnow():
        return jsonify(success=False, error='Verification code has expired.'), 400
    
    # Find the user
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify(success=False, error='User not found.'), 400
    
    # Update password
    user.set_password(new_password)
    db.session.commit()
    
    # Mark OTP as verified
    otp_record.verified = True
    db.session.commit()
    
    # Send confirmation email
    confirm_html = get_email_template(
        title='Password Reset Successful',
        content=f'''
          <p style="margin-bottom: 20px;">Hello {user.first_name},</p>
          <p style="margin-bottom: 20px;">Your GLOBALEASYTRANSASSET password has been successfully reset.</p>
          <p style="color: #6B7280; font-size: 14px;">If you didn't make this change, please contact support immediately.</p>
        ''',
        button_text='Go to Login',
        button_url='http://127.0.0.1:5000/login'
    )
    send_email(
        to_email=email,
        subject='Your GLOBALEASYTRANSASSET password has been reset',
        html_content=confirm_html
    )
    
    return jsonify(success=True, message='Password reset successfully!'), 200


# ═══════════════════════════ ADMIN API ENDPOINTS ═══════════════════════════

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify(success=False, error='Admin access required'), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/admin/users')
@require_admin
def admin_get_users():
    """Get all users for admin panel"""
    users = User.query.order_by(User.created_at.desc()).all()
    user_list = []
    for user in users:
        total_balance = sum(acc.balance for acc in user.accounts) if user.accounts else 0
        initials = f"{user.first_name[0]}{user.last_name[0]}" if user.first_name and user.last_name else "??"
        colors = ['#1E6BFF','#22C55E','#8B5CF6','#F59E0B','#EF4444','#4DA3FF','#0B3D91','#16a34a']
        user_list.append({
            'id': f'GA-{user.id:05d}',
            'accountNumber': user.account_number,
            'name': f"{user.first_name} {user.last_name}",
            'email': user.email,
            'country': '',
            'balance': total_balance,
            'kyc': 'verified' if user.status == 'Active' else 'pending',
            'status': user.status.lower(),
            'joined': user.created_at.strftime('%b %d, %Y') if user.created_at else 'N/A',
            'cards': len(user.cards) if user.cards else 0,
            'initials': initials.upper(),
            'col': colors[user.id % len(colors)],
        })
    return jsonify(success=True, users=user_list), 200


@app.route('/api/admin/credits')
@require_admin
def admin_get_credits():
    credits = Transaction.query.filter(
        Transaction.direction == 'in'
    ).order_by(Transaction.created_at.desc()).limit(50).all()
    credit_list = []
    for txn in credits:
        credit_list.append({
            'user': f"{txn.user.first_name} {txn.user.last_name}" if txn.user else 'Unknown',
            'id': f'GA-{txn.user_id:05d}' if txn.user else 'N/A',
            'amount': txn.amount,
            'currency': txn.currency or 'USD',
            'reason': txn.details or 'Credit',
            'by': 'Admin',
            'date': txn.created_at.strftime('%b %d, %Y · %H:%M') if txn.created_at else 'N/A',
            'status': 'completed',
        })
    return jsonify(success=True, credits=credit_list), 200


@app.route('/api/admin/cards')
@require_admin
def admin_get_cards():
    cards = VirtualCard.query.order_by(VirtualCard.created_at.desc()).all()
    card_list = []
    colors = ['#1E6BFF','#22C55E','#8B5CF6','#F59E0B','#EF4444','#4DA3FF','#0B3D91','#16a34a']
    for card in cards:
        initials = f"{card.user.first_name[0]}{card.user.last_name[0]}" if card.user and card.user.first_name and card.user.last_name else "??"
        card_list.append({
            'id': f'CR-{card.id:03d}',
            'user': f"{card.user.first_name} {card.user.last_name}" if card.user else 'Unknown',
            'uid': f'GA-{card.user_id:05d}' if card.user else 'N/A',
            'type': 'Virtual Debit',
            'plan': 'Elite' if card.card_limit >= 100000 else 'Premium' if card.card_limit >= 25000 else 'Standard',
            'network': 'Visa',
            'requested': card.created_at.strftime('%b %d, %Y') if card.created_at else 'N/A',
            'status': card.status.lower(),
            'initials': initials.upper(),
            'col': colors[card.id % len(colors)],
        })
    return jsonify(success=True, cards=card_list), 200


@app.route('/api/admin/transfers')
@require_admin
def admin_get_transfers():
    transfers = Transaction.query.filter(
        Transaction.category == 'Transfer'
    ).order_by(Transaction.created_at.desc()).limit(50).all()
    transfer_list = []
    colors = ['#1E6BFF','#22C55E','#8B5CF6','#F59E0B','#EF4444','#4DA3FF','#0B3D91','#16a34a']
    for txn in transfers:
        initials = f"{txn.user.first_name[0]}{txn.user.last_name[0]}" if txn.user and txn.user.first_name and txn.user.last_name else "??"
        status = 'approved' if txn.status == 'Completed' else ('pending' if txn.status == 'pending' else 'flagged')
        transfer_list.append({
            'id': f'TXN-{txn.id:03d}',
            'sender': f"{txn.user.first_name} {txn.user.last_name}" if txn.user else 'Unknown',
            'uid': f'GA-{txn.user_id:05d}' if txn.user else 'N/A',
            'recipient': txn.details or 'N/A',
            'amount': f"${txn.amount:,.2f}",
            'currency': txn.currency or 'USD',
            'dest': txn.details or 'N/A',
            'method': 'SWIFT',
            'requested': txn.created_at.strftime('%b %d, %Y') if txn.created_at else 'N/A',
            'status': status,
            'initials': initials.upper(),
            'col': colors[txn.id % len(colors)],
        })
    return jsonify(success=True, transfers=transfer_list), 200


@app.route('/api/admin/activity')
@require_admin
def admin_get_activity():
    activities = Transaction.query.order_by(Transaction.created_at.desc()).limit(20).all()
    activity_list = []
    for txn in activities:
        if txn.direction == 'in':
            ico = 'rgba(34,197,94,.12)'
            color = '#22C55E'
            icon = '<polyline points="20 6 9 17 4 12"/>'
            title = f"Credit — {txn.user.first_name} {txn.user.last_name}" if txn.user else 'Credit'
            sub = f"${txn.amount} {txn.currency or 'USD'}"
        elif txn.category == 'Transfer':
            ico = 'rgba(30,107,255,.12)'
            color = '#1E6BFF'
            icon = '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>'
            title = f"Transfer — {txn.user.first_name} {txn.user.last_name}" if txn.user else 'Transfer'
            sub = f"${txn.amount} · {txn.details or 'N/A'}"
        else:
            ico = 'rgba(139,92,246,.12)'
            color = '#8B5CF6'
            icon = '<rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>'
            title = f"Transaction — {txn.tx_type or 'Unknown'}"
            sub = f"${txn.amount}"

        time_ago = 'Just now'
        if txn.created_at:
            diff = datetime.utcnow() - txn.created_at
            if diff.days > 0:
                time_ago = f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds > 3600:
                time_ago = f"{diff.seconds // 3600} hr ago"
            elif diff.seconds > 60:
                time_ago = f"{diff.seconds // 60} min ago"

        activity_list.append({
            'ico': ico, 'color': color, 'icon': icon,
            'title': title, 'sub': sub, 'time': time_ago,
        })
    return jsonify(success=True, activity=activity_list), 200


@app.route('/api/admin/overview')
@require_admin
def admin_get_overview():
    total_users = User.query.count()
    total_cards = VirtualCard.query.count()
    pending_cards = VirtualCard.query.filter_by(status='pending').count()
    total_transactions = Transaction.query.count()
    pending_transfers = Transaction.query.filter_by(
        category='Transfer', status='pending'
    ).count()
    total_balance = sum(acc.balance for acc in Account.query.all())

    return jsonify(success=True, overview={
        'totalUsers': total_users,
        'totalCards': total_cards,
        'pendingCards': pending_cards,
        'totalTransactions': total_transactions,
        'pendingTransfers': pending_transfers,
        'totalBalance': total_balance,
    }), 200

@app.route('/api/admin/card/<int:card_id>/<action>')
@require_admin
def admin_card_action(card_id, action):
    """Approve, reject, or freeze a card"""
    card = VirtualCard.query.get(card_id)
    if not card:
        return jsonify(success=False, error='Card not found'), 404
    
    if action == 'approve':
        card.status = 'active'
    elif action == 'reject':
        card.status = 'rejected'
    elif action == 'freeze':
        card.is_frozen = True
    else:
        return jsonify(success=False, error='Invalid action'), 400
    
    db.session.commit()
    return jsonify(success=True, message=f'Card {action}d successfully'), 200


@app.route('/api/admin/transfer/<int:transfer_id>/<action>')
@require_admin
def admin_transfer_action(transfer_id, action):
    """Approve or reject a transfer"""
    txn = Transaction.query.get(transfer_id)
    if not txn:
        return jsonify(success=False, error='Transfer not found'), 404
    
    if action == 'approve':
        txn.status = 'Completed'
        # Optionally, credit recipient here if needed
    elif action == 'reject':
        txn.status = 'Rejected'
    else:
        return jsonify(success=False, error='Invalid action'), 400
    db.session.commit()
    return jsonify(success=True, message=f'Transfer {action}d successfully'), 200


@app.route('/api/admin/user/<int:user_id>/<action>', methods=['GET', 'POST'])
@require_admin
def admin_user_action(user_id, action):
    """Suspend, activate, or credit a user account"""
    user = User.query.get(user_id)
    if not user:
        return jsonify(success=False, error='User not found'), 404
    
    if action == 'suspend':
        user.status = 'Suspended'
        db.session.commit()
    
    elif action == 'activate':
        user.status = 'Active'
        db.session.commit()
    
    elif action == 'credit':
        data = request.get_json(silent=True) or {}
        amount = float(data.get('amount', 0))
        currency = data.get('currency', 'USD')
        reason = data.get('reason', 'Admin credit')
        if amount > 0:
            account = Account.query.filter_by(user_id=user.id, currency=currency).first()
            if not account:
                account = Account(user_id=user.id, currency=currency, balance=0)
                db.session.add(account)
            account.balance += amount
            txn = Transaction(
                user_id=user.id,
                reference=generate_tx_ref(),
                tx_type='Admin Credit',
                date=datetime.now().strftime('%b %d'),
                category='Credit',
                amount=amount,
                currency=currency,
                direction='in',
                status='Completed',
                details=reason
            )
            db.session.add(txn)
            db.session.commit()

            # Send email notification to user
            credit_html = get_email_template(
                title='Account Credited',
                content=f'''
                  <p style="margin-bottom: 20px;">Hello {user.first_name},</p>
                  <p style="margin-bottom: 20px;">Your GLOBALEASYTRANSASSET account has been credited.</p>
                  <div style="background: #EBF2FF; padding: 24px; border-radius: 12px; text-align: center; margin: 20px 0;">
                    <div style="font-size: 36px; font-weight: 800; color: #1E6BFF;">+{currency} {amount:,.2f}</div>
                    <div style="font-size: 14px; color: #6B7280; margin-top: 8px;">Has been added to your account</div>
                  </div>
                  <div style="background: #F6F8FC; padding: 20px; border-radius: 12px; text-align: left; margin: 20px 0;">
                    <p style="margin: 0 0 10px; color: #6B7280; font-size: 14px;"><strong style="color: #0A0A0A;">Amount:</strong> {currency} {amount:,.2f}</p>
                    <p style="margin: 0 0 10px; color: #6B7280; font-size: 14px;"><strong style="color: #0A0A0A;">Reason:</strong> {reason}</p>
                    <p style="margin: 0; color: #6B7280; font-size: 14px;"><strong style="color: #0A0A0A;">Date:</strong> {datetime.now().strftime("%b %d, %Y · %H:%M UTC")}</p>
                  </div>
                  <p style="color: #6B7280; font-size: 14px;">Log in to your dashboard to view your updated balance.</p>
                ''',
                button_text='View Dashboard',
                button_url='http://127.0.0.1:5000/dashboard',
                to_email=user.email
            )
            send_email(
                to_email=user.email,
                subject=f'Your account has been credited {currency} {amount:,.2f}',
                html_content=credit_html
            )
        else:
            return jsonify(success=False, error='Amount must be greater than 0'), 400
    
    else:
        return jsonify(success=False, error='Invalid action'), 400
    
    return jsonify(success=True, message=f'User {action} successful'), 200


# ═══════════════════════════ INITIALIZATION ═══════════════════════════

# Initialize database tables on startup
with app.app_context():
    db.create_all()
    
    # Migration: Add missing columns to existing tables
    from sqlalchemy import inspect
    
    inspector = inspect(db.engine)
    
    # Get existing columns in users table
    user_columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Define all columns that should exist in users table
    user_migrations = {
        'is_admin': 'BOOLEAN DEFAULT 0',
        'transaction_pin': 'VARCHAR(4) DEFAULT \'\'',
    }
    
    for col_name, col_def in user_migrations.items():
        if col_name not in user_columns:
            print(f"Migrating: Adding '{col_name}' column to users table...")
            db.session.execute(db.text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
            db.session.commit()
            print(f"✅ Migration complete: '{col_name}' column added")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Migration: Add missing columns to existing tables
        from sqlalchemy import inspect
        
        inspector = inspect(db.engine)
        
        # Get existing columns in users table
        user_columns = [col['name'] for col in inspector.get_columns('users')]
        
        # Define all columns that should exist in users table
        user_migrations = {
            'is_admin': 'BOOLEAN DEFAULT 0',
            'transaction_pin': 'VARCHAR(4) DEFAULT \'\'',
        }
        
        for col_name, col_def in user_migrations.items():
            if col_name not in user_columns:
                print(f"Migrating: Adding '{col_name}' column to users table...")
                db.session.execute(db.text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                db.session.commit()
                print(f"✅ Migration complete: '{col_name}' column added")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
