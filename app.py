from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import random
import string
import sqlite3
from datetime import datetime, timedelta
import hashlib
import secrets
import re
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
from translations import translator, t

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dadaal_secret_key_2025_change_in_production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Make translation function available in templates
@app.context_processor
def inject_translation():
    return dict(t=t, current_lang=translator.get_language())

# Security functions
def hash_password(password):
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt + password_hash.hex()

def verify_password(stored_password, provided_password):
    """Verify password against hash"""
    if not stored_password:
        return False
    salt = stored_password[:32]
    stored_hash = stored_password[32:]
    password_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt.encode(), 100000)
    return password_hash.hex() == stored_hash

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number"""
    pattern = r'^\+?[1-9]\d{1,14}$'
    return re.match(pattern, phone) is not None

def sanitize_input(text):
    """Basic input sanitization"""
    if not text:
        return ""
    return text.strip()[:1000]  # Limit length and strip whitespace

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Fadlan gal akoonkaaga si aad u aragto boggan.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin', False):
            flash('Ma lihid fasax si aad u aragto boggan.')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def generate_secure_token():
    """Generate secure random token"""
    return secrets.token_urlsafe(32)

def send_reset_email(email, reset_token):
    """Send password reset email"""
    try:
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        gmail_user = os.environ.get('GMAIL_USER')  # Your Gmail address
        gmail_password = os.environ.get('GMAIL_APP_PASSWORD')  # Gmail App Password

        reset_link = f"https://dadaal.onrender.com/reset_password/{reset_token}"

        if not gmail_user or not gmail_password:
            print(f"⚠️ Gmail credentials not configured!")
            print(f"Reset link for {email}: {reset_link}")
            # For demo mode, show link in flash message
            flash(f"Demo Mode: Password reset link-kaaga: {reset_link}")
            return False  # Return False to indicate email wasn't sent

        # Email content
        subject = "Dadaal App - Password Reset"
        body = f"""
        Salaan,

        Waxaad codsatay in password-kaaga la bedelo.

        Riix link-kan hoose si aad password cusub u samaysato:
        {reset_link}

        Link-kani wuxuu shaqeyn doonaa 1 saac gudahood.

        Haddii aadan codsan password reset, iska indho tir farriintan.

        Mahadsanid,
        Kooxda Dadaal App
        """

        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(gmail_user, gmail_password)
        text = msg.as_string()
        server.sendmail(gmail_user, email, text)
        server.quit()

        print(f"Password reset email sent successfully to {email}")
        return True

    except Exception as e:
        print(f"Email sending error: {e}")
        print(f"Fallback: Password reset link for {email}: {reset_link}")
        return True  # Return True for demo purposes

def send_verification_email(email, verification_code):
    """Send email verification code"""
    try:
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        gmail_user = os.environ.get('GMAIL_USER')  # Your Gmail address
        gmail_password = os.environ.get('GMAIL_APP_PASSWORD')  # Gmail App Password

        if not gmail_user or not gmail_password:
            print(f"Gmail credentials not configured. Verification code for {email}: {verification_code}")
            # For Render deployment, show code on screen if email fails
            from flask import flash
            flash(f"Demo Mode: Verification code-kaagu waa: {verification_code}")
            return True  # Return True for demo purposes

        # Email content
        subject = "Dadaal App - Email Xaqiijinta Code-ka"
        body = f"""
        Ku soo dhawow Dadaal App!

        Code-ka email xaqiijinta: {verification_code}

        Gali code-kan si aad u dhammaystirto diiwaan galinta.

        Code-ku wuxuu dhici doonaa 10 daqiiqo gudahood.

        Mahadsanid!
        Kooxda Dadaal App
        """

        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(gmail_user, gmail_password)
        text = msg.as_string()
        server.sendmail(gmail_user, email, text)
        server.quit()

        print(f"Verification email sent successfully to {email}")
        return True

    except Exception as e:
        print(f"Email verification sending error: {e}")
        print(f"Fallback: Verification code for {email}: {verification_code}")
        return True  # Return True for demo purposes

def generate_verification_code():
    """Generate 6-digit verification code"""
    return str(random.randint(100000, 999999))

# Database setup
def init_db():
    conn = sqlite3.connect('dadaal.db')
    cursor = conn.cursor()

    # Users table with enhanced fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL DEFAULT '',
            total_earnings REAL DEFAULT 0,
            referral_code TEXT UNIQUE,
            referrer_id INTEGER,
            status TEXT DEFAULT 'active',
            premium_until DATE,
            email_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referrer_id) REFERENCES users (id)
        )
    ''')

    # Transactions table with enhanced tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('earning', 'withdrawal', 'referral', 'premium', 'bonus')),
            status TEXT DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
            description TEXT,
            reference_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Contact messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'new' CHECK (status IN ('new', 'read', 'replied', 'closed')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Referrals tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'invalid')),
            commission_earned REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referrer_id) REFERENCES users (id),
            FOREIGN KEY (referred_id) REFERENCES users (id)
        )
    ''')

    # Affiliate links table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS affiliate_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            link_code TEXT UNIQUE NOT NULL,
            clicks INTEGER DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            commission_rate REAL DEFAULT 0.20,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Password reset tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Email verification codes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_verification_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # User activity logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Wholesale partners table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wholesale_partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            company_name TEXT NOT NULL,
            contact_person TEXT NOT NULL,
            business_email TEXT NOT NULL,
            business_phone TEXT,
            website TEXT,
            business_type TEXT NOT NULL,
            product_category TEXT NOT NULL,
            business_description TEXT,
            monthly_volume REAL DEFAULT 0,
            commission_tier TEXT DEFAULT 'bronze',
            status TEXT DEFAULT 'pending',
            approved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Wholesale products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wholesale_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            wholesale_price REAL,
            category TEXT,
            sku TEXT UNIQUE,
            stock_quantity INTEGER DEFAULT 0,
            commission_rate REAL DEFAULT 0.15,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (partner_id) REFERENCES wholesale_partners (id)
        )
    ''')

    # Wholesale sales table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wholesale_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            partner_id INTEGER NOT NULL,
            buyer_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_amount REAL NOT NULL,
            commission_amount REAL NOT NULL,
            commission_rate REAL NOT NULL,
            status TEXT DEFAULT 'completed',
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES wholesale_products (id),
            FOREIGN KEY (partner_id) REFERENCES wholesale_partners (id),
            FOREIGN KEY (buyer_id) REFERENCES users (id)
        )
    ''')

    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_affiliate_user ON affiliate_links(user_id)')

    conn.commit()
    conn.close()

# Database migration function
def migrate_database():
    """Migrate existing database to new schema"""
    conn = sqlite3.connect('dadaal.db')
    cursor = conn.cursor()

    try:
        # Check if password_hash column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'password_hash' not in columns:
            # Add missing columns to users table one by one
            columns_to_add = [
                ('password_hash', 'TEXT NOT NULL DEFAULT ""'),
                ('total_earnings', 'REAL DEFAULT 0'),
                ('referral_code', 'TEXT'),
                ('referrer_id', 'INTEGER'),
                ('status', 'TEXT DEFAULT "active"'),
                ('premium_until', 'DATE'),
                ('email_verified', 'BOOLEAN DEFAULT 0'),
                ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
                ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            ]

            for col_name, col_definition in columns_to_add:
                try:
                    cursor.execute(f'ALTER TABLE users ADD COLUMN {col_name} {col_definition}')
                    print(f"Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"Column {col_name} already exists")
                    else:
                        print(f"Error adding column {col_name}: {e}")

        # Check and add user_activity_logs table if it doesn't exist
        cursor.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name='user_activity_logs'
        ''')

        if not cursor.fetchone():  # Table doesn't exist
            cursor.execute('''
                CREATE TABLE user_activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    activity_type TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            print("user_activity_logs table created successfully!")

        conn.commit()
        print("Database migration completed successfully!")

    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

# Initialize database
init_db()
migrate_database()

# Global variables for tracking earnings
total_earnings = 0
user_referrals = {}
affiliate_earnings = 0

# Analytics functions
def log_user_activity(user_id, activity_type, description):
    """Log user activity to database."""
    try:
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_activity_logs (user_id, activity_type, description)
            VALUES (?, ?, ?)
        ''', (user_id, activity_type, description))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging user activity: {e}")

@app.route('/set_language/<language>')
def set_language(language):
    if translator.set_language(language):
        flash(f'Language changed to {language}')
    else:
        flash('Language not supported')

    # Redirect back to the previous page or home
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    return render_template('index.html', earnings=total_earnings)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')

        # Admin password from environment variable for security
        admin_password = os.environ.get('ADMIN_PASSWORD', 'dadaal_admin_2025')
        if password == admin_password:
            session['is_admin'] = True
            session.permanent = True
            flash('Admin-ka si guul leh ayaad u gashay!')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Password-ku khalad yahay!')
            return render_template('admin.html')

    # Check if already logged in as admin
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))

    return render_template('admin.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = sqlite3.connect('dadaal.db')
    cursor = conn.cursor()

    # Get total platform stats
    cursor.execute('SELECT COUNT(*), SUM(total_earnings) FROM users WHERE status = "active"')
    user_stats = cursor.fetchone()

    cursor.execute('SELECT COUNT(*) FROM contact_messages WHERE status = "new"')
    new_messages = cursor.fetchone()[0]

    cursor.execute('SELECT SUM(amount) FROM transactions WHERE type = "earning"')
    total_earnings_db = cursor.fetchone()[0] or 0

    cursor.execute('SELECT SUM(commission_earned) FROM referrals WHERE status = "completed"')
    affiliate_earnings_db = cursor.fetchone()[0] or 0

    # Get all users with detailed info
    cursor.execute('''
        SELECT id, name, email, phone, total_earnings, status, premium_until, created_at 
        FROM users 
        ORDER BY created_at DESC
    ''')
    all_users = cursor.fetchall()

    # Get recent transactions
    cursor.execute('''
        SELECT t.amount, t.type, t.description, t.created_at, u.name 
        FROM transactions t 
        JOIN users u ON t.user_id = u.id 
        ORDER BY t.created_at DESC LIMIT 10
    ''')
    recent_transactions = cursor.fetchall()

    conn.close()

    return render_template('admin_dashboard.html', 
                         user_stats=user_stats,
                         new_messages=new_messages,
                         total_earnings=total_earnings_db, 
                         affiliate_earnings=affiliate_earnings_db,
                         all_users=all_users,
                         recent_transactions=recent_transactions)

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        # Get user's earnings and stats
        cursor.execute('''
            SELECT total_earnings, referral_code, premium_until, name, email
            FROM users WHERE id = ?
        ''', (session['user_id'],))
        user_data = cursor.fetchone()

        if not user_data:
            flash('Akoonkaaga lama helin. Fadlan mar kale gal.')
            return redirect(url_for('login'))

        # Get recent transactions
        cursor.execute('''
            SELECT amount, type, description, created_at 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 10
        ''', (session['user_id'],))
        transactions = cursor.fetchall()

        # Get referral stats
        cursor.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(commission_earned), 0) as total
            FROM referrals 
            WHERE referrer_id = ? AND status = "completed"
        ''', (session['user_id'],))
        referral_stats = cursor.fetchone()

        conn.close()

        return render_template('dashboard.html', 
                             user_data=user_data,
                             transactions=transactions,
                             referral_stats=referral_stats)

    except Exception as e:
        flash('Khalad ayaa dhacay dashboard-ka la keenayay.')
        print(f"Dashboard error: {e}")
        return redirect(url_for('home'))

@app.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    # Check if this is a premium payment
    is_premium = request.args.get('type') == 'premium'
    premium_plan = request.args.get('plan', 'monthly')
    premium_amount = request.args.get('amount', '19.99')

    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        phone = sanitize_input(request.form.get('phone', ''))
        payment_method = sanitize_input(request.form.get('payment_method', 'mobile_money'))

        if amount <= 0:
            flash('Fadlan geli lacag sax ah.')
            return redirect(url_for('payment'))

        if not phone:
            flash('Fadlan geli nambarka telefoonka.')
            return redirect(url_for('payment'))

        try:
            # Process real payment based on method
            payment_success = False
            payment_response = {}

            if payment_method == 'mobile_money':
                # Somalia Mobile Money Integration (EVC PLUS, ZAAD, etc.)
                payment_response = process_mobile_money_payment(amount, phone)
                payment_success = payment_response.get('success', False)

            elif payment_method == 'credit_card':
                # Stripe Credit Card Processing
                payment_response = process_stripe_payment(amount, request.form)
                payment_success = payment_response.get('success', False)

            elif payment_method == 'bank_transfer':
                # Bank transfer processing
                payment_response = process_bank_transfer(amount, phone)
                payment_success = payment_response.get('success', False)

            if payment_success:
                conn = sqlite3.connect('dadaal.db')
                cursor = conn.cursor()

                # Generate unique reference ID
                reference_id = payment_response.get('transaction_id', f"PAY-{secrets.token_hex(8).upper()}")

                # Log payment processing
                print(f"Processing payment: ${amount} via {payment_method} for user {session['user_id']}")

                # Check if this is a premium payment
                if is_premium:
                    # Calculate premium duration
                    if premium_plan == 'monthly':
                        premium_days = 30
                    else:  # yearly
                        premium_days = 365

                    # Calculate premium expiry date
                    premium_until = datetime.now() + timedelta(days=premium_days)

                    # Insert premium transaction
                    cursor.execute('''
                        INSERT INTO transactions (user_id, amount, type, status, description, reference_id)
                        VALUES (?, ?, 'premium', 'completed', ?, ?)
                    ''', (session['user_id'], amount, f'Premium subscription - {premium_plan} plan', reference_id))

                    # Update user's premium status
                    cursor.execute('''
                        UPDATE users SET premium_until = ?
                        WHERE id = ?
                    ''', (premium_until.date(), session['user_id']))

                    flash(f'Guul! Premium {premium_plan} plan waa la activation gareeyay ilaa {premium_until.strftime("%Y-%m-%d")}!')
                else:
                    # Regular payment - Calculate commission (5% of payment)
                    commission = amount * 0.05

                    # Insert payment transaction
                    payment_description = f'Commission from ${amount} payment via {payment_method.replace("_", " ").title()}'
                    cursor.execute('''
                        INSERT INTO transactions (user_id, amount, type, status, description, reference_id)
                        VALUES (?, ?, 'earning', 'completed', ?, ?)
                    ''', (session['user_id'], commission, payment_description, reference_id))

                    # Update user's total earnings
                    cursor.execute('''
                        UPDATE users SET total_earnings = total_earnings + ?
                        WHERE id = ?
                    ''', (commission, session['user_id']))

                    # Update global earnings
                    global total_earnings
                    total_earnings += commission

                    flash(f'Guul! Lacagtaada ${amount} si guul leh ayaa loo aqbalay. Commission ${commission:.2f} ayaa lagugu daray.')

                conn.commit()
                conn.close()

                # Log payment activity
                log_user_activity(session['user_id'], 'payment', f'Payment of ${amount} via {payment_method}')

                return redirect(url_for('thankyou'))
            else:
                error_msg = payment_response.get('error', 'Payment failed')
                flash(f'Lacag bixintu way fashilmay: {error_msg}')
                return redirect(url_for('payment'))

        except Exception as e:
            flash(f'Khalad ayaa dhacay lacag bixinta: {str(e)}')
            print(f"Payment processing error: {e}")
            return redirect(url_for('payment'))

    return render_template('payment.html')

def process_mobile_money_payment(amount, phone):
    """Process Mobile Money payment for Somalia (EVC PLUS, ZAAD Service)"""
    try:
        print(f"Processing Mobile Money payment: ${amount} to {phone}")

        # Clean phone number
        phone = phone.strip().replace('-', '').replace(' ', '')

        # Validate phone number format for Somalia
        if not (phone.startswith('+252') or phone.startswith('252')):
            return {
                'success': False,
                'error': 'Nambarka telefoonka waa inuu bilaabmaa +252 (tusaale: +252611234567)'
            }

        # Clean and validate phone number length
        clean_phone = phone.replace('+252', '').replace('252', '').replace(' ', '').replace('-', '')

        # Somalia phone numbers: 61XXXXXXX (Hormuud), 63XXXXXXX (Somtel), etc.
        if not (len(clean_phone) == 9 and clean_phone.startswith(('61', '62', '63', '65', '90'))):
            return {
                'success': False,
                'error': 'Nambarka telefoonka format khalad. Tusaale sax ah: +252611234567'
            }

        # Validate amount
        if amount < 1 or amount > 10000:
            return {
                'success': False,
                'error': 'Lacagta waa inay u dhaxaysaa $1 - $10,000'
            }

        # Simulate successful API call
        transaction_id = f"MM-{secrets.token_hex(8).upper()}"

        print(f"✅ Mobile Money payment successful: {transaction_id}")

        return {
            'success': True,
            'transaction_id': transaction_id,
            'message': f'Mobile Money payment ${amount} guul leh - {phone}',
            'payment_method': 'mobile_money'
        }

    except Exception as e:
        print(f"❌ Mobile money payment error: {e}")
        return {
            'success': False,
            'error': f'Khalad ayaa dhacay lacag bixinta: {str(e)}'
        }

def process_stripe_payment(amount, form_data):
    """Process Stripe credit card payment"""
    try:
        # Demo mode - simulate successful payment
        print(f"Processing Stripe payment: ${amount}")

        cardholder_name = form_data.get('cardholder_name', '')
        billing_email = form_data.get('billing_email', '')

        if not cardholder_name or not billing_email:
            return {
                'success': False,
                'error': 'Fadlan buuxi magaca iyo email-ka'
            }

        # Simulate successful payment
        transaction_id = f"STRIPE-{secrets.token_hex(8).upper()}"

        return {
            'success': True,
            'transaction_id': transaction_id,
            'message': f'Credit card payment ${amount} guul leh'
        }

    except Exception as e:
        print(f"Stripe payment error: {e}")
        return {
            'success': False,
            'error': 'Credit card payment wuu fashilmay'
        }

def process_bank_transfer(amount, phone):
    """Process bank transfer payment"""
    try:
        # Bank transfer processing logic
        # This would typically involve creating a pending transfer
        # and waiting for confirmation from the bank

        reference_id = f"BANK-{secrets.token_hex(8).upper()}"

        # For demo, we'll return a pending status
        return {
            'success': True,
            'transaction_id': reference_id,
            'message': 'Bank transfer initiated - pending confirmation'
        }

    except Exception as e:
        print(f"Bank transfer error: {e}")
        return {
            'success': False,
            'error': 'Bank transfer failed'
        }

def process_crypto_payment(amount, crypto_type, wallet_address):
    """Process cryptocurrency payment"""
    try:
        # Validate crypto type
        supported_cryptos = ['bitcoin', 'ethereum', 'usdt', 'bnb']
        if crypto_type.lower() not in supported_cryptos:
            return {
                'success': False,
                'error': f'Cryptocurrency {crypto_type} lama taageero'
            }

        # Validate wallet address format (basic validation)
        if len(wallet_address) < 26 or len(wallet_address) > 62:
            return {
                'success': False,
                'error': 'Wallet address format khalad'
            }

        # Generate transaction ID
        transaction_id = f"CRYPTO-{crypto_type.upper()}-{secrets.token_hex(8).upper()}"

        # Simulate crypto payment processing
        print(f"Processing {crypto_type} payment: ${amount} to {wallet_address}")

        # In production, integrate with crypto APIs:
        # - Coinbase Commerce API
        # - BitPay API
        # - Blockchain.info API

        return {
            'success': True,
            'transaction_id': transaction_id,
            'message': f'{crypto_type.title()} payment ${amount} si guul leh ayaa loo qabtay',
            'crypto_address': wallet_address,
            'amount_crypto': amount / get_crypto_rate(crypto_type)  # Convert USD to crypto
        }

    except Exception as e:
        print(f"Crypto payment error: {e}")
        return {
            'success': False,
            'error': f'Cryptocurrency payment failed: {str(e)}'
        }

def get_crypto_rate(crypto_type):
    """Get current crypto exchange rate (demo rates)"""
    # In production, integrate with CoinGecko or CryptoCompare API
    demo_rates = {
        'bitcoin': 45000,
        'ethereum': 2800,
        'usdt': 1.00,
        'bnb': 320
    }
    return demo_rates.get(crypto_type.lower(), 1)

# Real Affiliate Marketing Integration
import requests
import json

def get_alibaba_products(category="electronics", limit=50):
    """Get real Alibaba products via API"""
    try:
        # Alibaba API (requires API key)
        # For now, we'll use sample data that mimics real structure
        sample_products = [
            {
                'id': 'ALB001',
                'name': 'Wireless Bluetooth Headphones',
                'price': 15.99,
                'commission_rate': 0.08,  # 8% commission
                'supplier': 'Shenzhen Tech Co.',
                'image_url': 'https://example.com/headphones.jpg',
                'affiliate_url': 'https://www.alibaba.com/product-detail/...',
                'category': 'Electronics'
            },
            {
                'id': 'ALB002', 
                'name': 'Smart Phone Case iPhone 15',
                'price': 8.50,
                'commission_rate': 0.12,  # 12% commission
                'supplier': 'Guangzhou Mobile Accessories',
                'image_url': 'https://example.com/phonecase.jpg',
                'affiliate_url': 'https://www.alibaba.com/product-detail/...',
                'category': 'Electronics'
            },
            {
                'id': 'ALB003',
                'name': 'LED Strip Lights 5M RGB',
                'price': 12.99,
                'commission_rate': 0.15,  # 15% commission
                'supplier': 'Dongguan LED Factory',
                'image_url': 'https://example.com/ledstrip.jpg',
                'affiliate_url': 'https://www.alibaba.com/product-detail/...',
                'category': 'Home & Garden'
            },
            {
                'id': 'ALB004',
                'name': 'Fitness Tracker Smart Watch',
                'price': 25.99,
                'commission_rate': 0.10,  # 10% commission
                'supplier': 'Shenzhen Wearable Tech',
                'image_url': 'https://example.com/smartwatch.jpg',
                'affiliate_url': 'https://www.alibaba.com/product-detail/...',
                'category': 'Electronics'
            },
            {
                'id': 'ALB005',
                'name': 'Kitchen Silicone Utensils Set',
                'price': 18.99,
                'commission_rate': 0.20,  # 20% commission
                'supplier': 'Yangjiang Kitchenware Co.',
                'image_url': 'https://example.com/utensils.jpg',
                'affiliate_url': 'https://www.alibaba.com/product-detail/...',
                'category': 'Home & Kitchen'
            }
        ]

        return sample_products[:limit]
    except Exception as e:
        print(f"Alibaba API error: {e}")
        return []

def get_amazon_products(keyword="electronics", limit=20):
    """Get Amazon products via Amazon Associates API"""
    try:
        # Amazon Associates API integration would go here
        # For now, using sample data that mimics real Amazon structure
        sample_products = [
            {
                'id': 'AMZ001',
                'name': 'Apple AirPods Pro (2nd Generation)',
                'price': 249.99,
                'commission_rate': 0.04,  # 4% commission (Amazon's typical rate)
                'brand': 'Apple',
                'image_url': 'https://example.com/airpods.jpg',
                'affiliate_url': 'https://amazon.com/dp/B0BDHWDR12?tag=dadaal-20',
                'category': 'Electronics',
                'rating': 4.5,
                'reviews': 89234
            },
            {
                'id': 'AMZ002',
                'name': 'Samsung Galaxy S24 Ultra',
                'price': 1199.99,
                'commission_rate': 0.02,  # 2% commission
                'brand': 'Samsung',
                'image_url': 'https://example.com/samsung.jpg',
                'affiliate_url': 'https://amazon.com/dp/B0CMDRCG4Q?tag=dadaal-20',
                'category': 'Electronics',
                'rating': 4.4,
                'reviews': 12456
            },
            {
                'id': 'AMZ003',
                'name': 'Instant Pot Duo 7-in-1 Electric Pressure Cooker',
                'price': 79.99,
                'commission_rate': 0.08,  # 8% commission
                'brand': 'Instant Pot',
                'image_url': 'https://example.com/instantpot.jpg',
                'affiliate_url': 'https://amazon.com/dp/B00FLYWNYQ?tag=dadaal-20',
                'category': 'Home & Kitchen',
                'rating': 4.6,
                'reviews': 156789
            }
        ]

        return sample_products[:limit]
    except Exception as e:
        print(f"Amazon API error: {e}")
        return []

def track_affiliate_click(user_id, product_id, platform):
    """Track affiliate link clicks"""
    try:
        conn = sqlite3.connect('dadaal.db', timeout=20.0)
        cursor = conn.cursor()

        # Create affiliate clicks table if doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliate_clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                converted BOOLEAN DEFAULT 0,
                commission_earned REAL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Record the click
        cursor.execute('''
            INSERT INTO affiliate_clicks (user_id, product_id, platform)
            VALUES (?, ?, ?)
        ''', (user_id, product_id, platform))

        conn.commit()
        conn.close()

        return True
    except Exception as e:
        print(f"Affiliate click tracking error: {e}")
        return False

def process_affiliate_commission(user_id, product_id, sale_amount, commission_rate):
    """Process real affiliate commission when sale happens"""
    try:
        commission_amount = sale_amount * commission_rate

        conn = sqlite3.connect('dadaal.db', timeout=20.0)
        cursor = conn.cursor()

        # Add commission to user's earnings
        cursor.execute('''
            UPDATE users SET total_earnings = total_earnings + ?
            WHERE id = ?
        ''', (commission_amount, user_id))

        # Record the transaction
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, description, status)
            VALUES (?, ?, 'earning', ?, 'completed')
        ''', (user_id, commission_amount, f'Affiliate commission - Product {product_id}'))

        # Update affiliate click record
        cursor.execute('''
            UPDATE affiliate_clicks 
            SET converted = 1, commission_earned = ?
            WHERE user_id = ? AND product_id = ?
        ''', (commission_amount, user_id, product_id))

        conn.commit()
        conn.close()

        print(f"✅ Affiliate commission processed: ${commission_amount} for user {user_id}")
        return True

    except Exception as e:
        print(f"Commission processing error: {e}")
        return False


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = sanitize_input(request.form.get('name'))
        email = sanitize_input(request.form.get('email'))
        phone = sanitize_input(request.form.get('phone'))
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        referral_code = sanitize_input(request.form.get('referral_code', ''))

        # Validation
        if not all([name, email, password]):
            flash('Fadlan buuxi dhammaan qeybaha muhiimka ah.')
            return redirect(url_for('register'))

        if not validate_email(email):
            flash('Email-ka waa khalad.')
            return redirect(url_for('register'))

        if phone and not validate_phone(phone):
            flash('Nambarka telefoonka waa khalad.')
            return redirect(url_for('register'))

        if len(password) < 8:
            flash('Password-ku waa inuu ka badan yahay 8 xaraf.')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Password-yada ma isku mid aha.')
            return redirect(url_for('register'))

        try:
            # Check if email exists
            conn = sqlite3.connect('dadaal.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                flash('Email-kan horay ayaa loo isticmaalay.')
                conn.close()
                return redirect(url_for('register'))
        except Exception as e:
            flash('Khalad ayaa dhacay database-ka. Fadlan isku day mar kale.')
            print(f"Database error during registration: {e}")
            return redirect(url_for('register'))

        # Find referrer if referral code provided
        referrer_id = None
        if referral_code:
            cursor.execute('SELECT id FROM users WHERE referral_code = ?', (referral_code,))
            referrer = cursor.fetchone()
            if referrer:
                referrer_id = referrer[0]

        # Generate verification code
        verification_code = generate_verification_code()
        expires_at = datetime.now() + timedelta(minutes=10)  # Code expires in 10 minutes

        try:
            # Store verification code
            cursor.execute('''
                INSERT INTO email_verification_codes (email, code, expires_at)
                VALUES (?, ?, ?)
            ''', (email, verification_code, expires_at))

            # Send verification email
            if send_verification_email(email, verification_code):
                # Store user data temporarily in session for verification
                session['pending_user'] = {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'password_hash': hash_password(password),
                    'referral_code': f"DADAAL-{random.randint(10000, 99999)}",
                    'referrer_id': referrer_id
                }

                conn.commit()
                conn.close()

                flash(f'Verification code waxaa lagu diray {email}. Fadlan hubi email-kaaga oo gali code-ka.')
                return redirect(url_for('verify_email'))
            else:
                flash('Khalad ayaa dhacay email-ka dirista. Fadlan isku day mar kale.')
                conn.close()
                return redirect(url_for('register'))

        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'Khalad ayaa dhacay akoonka samayniisa: {str(e)}')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email'))

        if not email or not validate_email(email):
            flash('Fadlan geli email sax ah.')
            return render_template('forgot_password.html')

        try:
            conn = sqlite3.connect('dadaal.db')
            cursor = conn.cursor()

            # Check if user exists
            cursor.execute('SELECT id, name FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

            if user:
                # Generate reset token
                reset_token = secrets.token_urlsafe(32)
                expires_at = datetime.now() + timedelta(hours=1)  # Token expires in 1 hour

                # Save reset token
                cursor.execute('''
                    INSERT INTO password_reset_tokens (user_id, token, expires_at)
                    VALUES (?, ?, ?)
                ''', (user[0], reset_token, expires_at))

                conn.commit()

                # Send reset email
                if send_reset_email(email, reset_token):
                    flash('Fariinta password reset-ka waxaa lagu diray email-kaaga. Hubi email-kaaga.')
                else:
                    flash('Khalad ayaa dhacay email-ka dirista. Fadlan isku day mar kale.')
            else:
                # Don't reveal if email exists or not for security
                flash('Haddii email-kaan jiro, fariinta password reset waxaa lagu diray email-kaaga.')

            conn.close()
            return redirect(url_for('forgot_password'))

        except Exception as e:
            flash('Khalad ayaa dhacay. Fadlan isku day mar kale.')
            print(f"Forgot password error: {e}")
            return render_template('forgot_password.html')

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        # Check if token is valid and not expired
        cursor.execute('''
            SELECT t.id, t.user_id, u.email, u.name
            FROM password_reset_tokens t
            JOIN users u ON t.user_id = u.id
            WHERE t.token = ? AND t.expires_at > ? AND t.used = 0
        ''', (token, datetime.now()))

        token_data = cursor.fetchone()

        if not token_data:
            flash('Password reset link-ku wuu dhacay ama waa la isticmaalay.')
            conn.close()
            return redirect(url_for('login'))

        if request.method == 'POST':
            new_password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if not new_password or len(new_password) < 8:
                flash('Password-ku waa inuu ka badan yahay 8 xaraf.')
                return render_template('reset_password.html', token=token)

            if new_password != confirm_password:
                flash('Password-yada ma isku mid aha.')
                return render_template('reset_password.html', token=token)

            # Update password
            password_hash = hash_password(new_password)
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                         (password_hash, token_data[1]))

            # Mark token as used
            cursor.execute('UPDATE password_reset_tokens SET used = 1 WHERE id = ?', 
                         (token_data[0],))

            conn.commit()
            conn.close()

            flash('Password-kaaga si guul leh ayaa loo beddelay! Hadda gal akoonkaaga.')
            return redirect(url_for('login'))

        conn.close()
        return render_template('reset_password.html', token=token, user_name=token_data[3])

    except Exception as e:
        flash('Khalad ayaa dhacay. Fadlan isku day mar kale.')
        print(f"Reset password error: {e}")
        return redirect(url_for('login'))

@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if 'pending_user' not in session:
        flash('Wax khalad ah ayaa dhacay. Fadlan mar kale diiwaan geli.')
        return redirect(url_for('register'))

    if request.method == 'POST':
        verification_code = sanitize_input(request.form.get('verification_code'))

        if not verification_code:
            flash('Fadlan gali verification code-ka.')
            return render_template('verify_email.html')

        try:
            conn = sqlite3.connect('dadaal.db')
            cursor = conn.cursor()

            # Check if verification code is valid
            cursor.execute('''
                SELECT id, email FROM email_verification_codes 
                WHERE email = ? AND code = ? AND expires_at > ? AND verified = 0
                ORDER BY created_at DESC LIMIT 1
            ''', (session['pending_user']['email'], verification_code, datetime.now()))

            verification_record = cursor.fetchone()

            if verification_record:
                # Mark code as verified
                cursor.execute('''
                    UPDATE email_verification_codes SET verified = 1 
                    WHERE id = ?
                ''', (verification_record[0],))

                # Create the user account
                user_data = session['pending_user']
                cursor.execute('''
                    INSERT INTO users (name, email, phone, password_hash, referral_code, referrer_id, email_verified)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (user_data['name'], user_data['email'], user_data['phone'], 
                      user_data['password_hash'], user_data['referral_code'], user_data['referrer_id']))

                user_id = cursor.lastrowid

                # Create referral record if applicable
                if user_data['referrer_id']:
                    cursor.execute('''
                        INSERT INTO referrals (referrer_id, referred_id, commission_earned)
                        VALUES (?, ?, ?)
                    ''', (user_data['referrer_id'], user_id, 5.00))

                    # Add referral bonus to referrer
                    cursor.execute('''
                        UPDATE users SET total_earnings = total_earnings + 5.00 
                        WHERE id = ?
                    ''', (user_data['referrer_id'],))

                conn.commit()

                # Clear pending user from session
                session.pop('pending_user', None)

                # Set user session
                session['user_id'] = user_id
                session['user_name'] = user_data['name']
                session.permanent = True

                # Log user activity
                log_user_activity(user_id, 'email_verified', f'Email verified: {user_data["email"]}')

                flash('Email-kaaga si guul leh ayaa loo xaqiijiyay! Akoonkaaga waa la sameeyay.')
                return redirect(url_for('dashboard'))
            else:
                flash('Verification code khalad ama wuu dhacay. Fadlan isku day mar kale.')
                conn.close()
                return render_template('verify_email.html')

        except Exception as e:
            flash('Khalad ayaa dhacay verification-ka. Fadlan isku day mar kale.')
            print(f"Email verification error: {e}")
            return render_template('verify_email.html')

    return render_template('verify_email.html', email=session['pending_user']['email'])

@app.route('/resend_verification', methods=['POST'])
def resend_verification():
    if 'pending_user' not in session:
        return {'success': False, 'error': 'No pending verification found'}

    try:
        email = session['pending_user']['email']
        verification_code = generate_verification_code()
        expires_at = datetime.now() + timedelta(minutes=10)

        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        # Insert new verification code
        cursor.execute('''
            INSERT INTO email_verification_codes (email, code, expires_at)
            VALUES (?, ?, ?)
        ''', (email, verification_code, expires_at))

        conn.commit()
        conn.close()

        # Send new verification email
        if send_verification_email(email, verification_code):
            return {'success': True, 'message': 'Verification code cusub waa la diray'}
        else:
            return {'success': False, 'error': 'Email sending failed'}

    except Exception as e:
        print(f"Resend verification error: {e}")
        return {'success': False, 'error': 'Technical error occurred'}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email'))
        password = request.form.get('password')

        if not email or not password:
            flash('Fadlan geli email iyo password.')
            return render_template('login.html')

        try:
            conn = sqlite3.connect('dadaal.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, password_hash, status FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            conn.close()

            if not user:
                flash('Email-kan ma jiro. Fadlan diiwaan geli.')
                return render_template('login.html')

            if user[3] != 'active':
                flash('Akoonkaaga waa la joojiyay. Fadlan la xiriir maamulka.')
                return render_template('login.html')

            if not user[2]:
                flash('Akoonkaaga ma laha password. Fadlan mar kale diiwaan geli.')
                return render_template('login.html')

            if verify_password(user[2], password):
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['is_admin'] = False  # Add admin check if needed
                session.permanent = True

                flash(f'Ku soo dhawow dib, {user[1]}!')
                return redirect(url_for('dashboard'))
            else:
                flash('Password khalad. Fadlan isku day mar kale.')
                return render_template('login.html')

        except Exception as e:
            flash('Khalad ayaa dhacay mareegta. Fadlan isku day mar kale.')
            print(f"Login error: {e}")
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Si guul leh ayaad ka baxday.')
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    conn = sqlite3.connect('dadaal.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, email, phone, total_earnings, referral_code, premium_until, created_at
        FROM users WHERE id = ?
    ''', (session['user_id'],))
    user_data = cursor.fetchone()

    # Get referral stats
    cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND status = "completed"', (session['user_id'],))
    referral_count = cursor.fetchone()[0]

    conn.close()

    return render_template('profile.html', user=user_data, referral_count=referral_count)



@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

@app.route('/gifts')
def gifts():
    return render_template('gifts.html')

@app.route('/ads')
def ads():
    return render_template('ads.html')

@app.route('/referral')
def referral():
    referral_code = f"DADAAL-{random.randint(1000, 9999)}"
    return render_template('referral.html', referral_code=referral_code)

@app.route('/track_referral', methods=['POST'])
def track_referral():
    data = request.get_json()
    referral_code = data.get('referral_code')
    action = data.get('action')  # 'signup', 'share', etc.

    # Here you would normally save to database
    global total_earnings
    if action == 'signup':
        total_earnings += 5.00  # $5 for successful referral
    elif action == 'share':
        total_earnings += 0.25  # $0.25 for sharing

    return {'success': True, 'earnings': total_earnings}

@app.route('/track_share', methods=['POST'])
def track_share():
    """Track social media sharing for analytics"""
    try:
        data = request.get_json()
        platform = data.get('platform')
        referral_code = data.get('referral_code')
        timestamp = data.get('timestamp')

        # Save sharing analytics to database
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        # Create shares table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                platform TEXT NOT NULL,
                referral_code TEXT,
                shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Insert share record
        user_id = session.get('user_id')
        cursor.execute('''
            INSERT INTO shares (user_id, platform, referral_code)
            VALUES (?, ?, ?)
        ''', (user_id, platform, referral_code))

        # Give small bonus for sharing (optional)
        if user_id:
            cursor.execute('''
                INSERT INTO transactions (user_id, amount, type, description)
                VALUES (?, ?, 'bonus', ?)
            ''', (user_id, 0.25, f'Sharing bonus - {platform}'))

            cursor.execute('''
                UPDATE users SET total_earnings = total_earnings + 0.25
                WHERE id = ?
            ''', (user_id,))

        conn.commit()
        conn.close()

        return {'success': True, 'message': 'Share tracked successfully'}

    except Exception as e:
        print(f"Share tracking error: {e}")
        return {'success': False, 'error': str(e)}

@app.route('/premium')
def premium():
    return render_template('premium.html')

@app.route('/process_premium', methods=['POST'])
@login_required
def process_premium():
    try:
        plan = request.form.get('plan')
        amount = float(request.form.get('amount'))

        # Redirect to payment page with premium parameters
        return redirect(url_for('payment', type='premium', plan=plan, amount=amount))

    except Exception as e:
        print(f"Premium processing error: {e}")
        flash('Khalad ayaa dhacay premium processing. Fadlan isku day mar kale.')
        return redirect(url_for('premium'))

@app.route('/vip_services')
@login_required
def vip_services():
    """VIP Services for high-paying customers"""
    return render_template('vip_services.html')

@app.route('/business_plans')
def business_plans():
    """Business subscription plans for companies"""
    return render_template('business_plans.html')

@app.route('/marketplace')
@login_required
def marketplace():
    """Digital marketplace for selling products/services"""
    try:
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        # Get marketplace items (create table if needed)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marketplace_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                category TEXT,
                image_url TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES users (id)
            )
        ''')

        # Get active marketplace items
        cursor.execute('''
            SELECT m.*, u.name as seller_name 
            FROM marketplace_items m 
            JOIN users u ON m.seller_id = u.id 
            WHERE m.status = 'active' 
            ORDER BY m.created_at DESC
        ''')
        marketplace_items = cursor.fetchall()

        # Get wholesale products
        cursor.execute('''
            SELECT wp.*, wpart.company_name as partner_name
            FROM wholesale_products wp
            JOIN wholesale_partners wpart ON wp.partner_id = wpart.id
            WHERE wp.status = 'active' AND wpart.status = 'approved'
            ORDER BY wp.created_at DESC
        ''')
        wholesale_products = cursor.fetchall()

        conn.commit()
        conn.close()

        return render_template('marketplace.html', 
                             items=marketplace_items,
                             wholesale_products=wholesale_products)

    except Exception as e:
        flash('Khalad ayaa dhacay marketplace-ka.')
        return redirect(url_for('dashboard'))

@app.route('/add_marketplace_item', methods=['POST'])
@login_required
def add_marketplace_item():
    """Add item to marketplace"""
    try:
        title = sanitize_input(request.form.get('title'))
        description = sanitize_input(request.form.get('description'))
        price = float(request.form.get('price'))
        category = sanitize_input(request.form.get('category'))

        if not title or price <= 0:
            flash('Fadlan buuxi macluumaadka item-ka.')
            return redirect(url_for('marketplace'))

        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO marketplace_items (seller_id, title, description, price, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], title, description, price, category))

        conn.commit()
        conn.close()

        flash(f'Item "{title}" waa la ku daray marketplace-ka!')
        return redirect(url_for('marketplace'))

    except Exception as e:
        flash('Khalad ayaa dhacay item-ka ku darista.')
        return redirect(url_for('marketplace'))

@app.route('/affiliate')
def affiliate():
    return render_template('affiliate.html')

@app.route('/real_affiliate')
@login_required
def real_affiliate():
    """Real affiliate marketing with Alibaba, Amazon integration"""
    try:
        # Get real products from different platforms
        alibaba_products = get_alibaba_products(limit=12)
        amazon_products = get_amazon_products(limit=8)

        # Get user's affiliate stats
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        # Get total affiliate earnings
        cursor.execute('''
            SELECT COALESCE(SUM(commission_earned), 0) 
            FROM affiliate_clicks 
            WHERE user_id = ? AND converted = 1
        ''', (session['user_id'],))
        affiliate_earnings = cursor.fetchone()[0]

        # Get clicks today
        cursor.execute('''
            SELECT COUNT(*) 
            FROM affiliate_clicks 
            WHERE user_id = ? AND DATE(clicked_at) = DATE('now')
        ''', (session['user_id'],))
        clicks_today = cursor.fetchone()[0]

        # Get conversions this month
        cursor.execute('''
            SELECT COUNT(*) 
            FROM affiliate_clicks 
            WHERE user_id = ? AND converted = 1 
            AND strftime('%Y-%m', clicked_at) = strftime('%Y-%m', 'now')
        ''', (session['user_id'],))
        conversions_month = cursor.fetchone()[0]

        conn.close()

        return render_template('real_affiliate.html',
                             alibaba_products=alibaba_products,
                             amazon_products=amazon_products,
                             affiliate_earnings=affiliate_earnings,
                             clicks_today=clicks_today,
                             conversions_month=conversions_month)

    except Exception as e:
        flash('Khalad ayaa dhacay affiliate marketing.')
        print(f"Real affiliate error: {e}")
        return redirect(url_for('affiliate'))

@app.route('/track_affiliate_click', methods=['POST'])
@login_required
def track_affiliate_click_route():
    """Track affiliate link clicks and actions"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        platform = data.get('platform')
        action = data.get('action', 'click')

        success = track_affiliate_click(session['user_id'], product_id, platform)

        if success:
            return {'success': True, 'message': 'Click tracked successfully'}
        else:
            return {'success': False, 'error': 'Failed to track click'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/affiliate_stats')
@login_required
def affiliate_stats():
    """Get real-time affiliate statistics"""
    try:
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        # Get comprehensive stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_clicks,
                COUNT(CASE WHEN converted = 1 THEN 1 END) as total_conversions,
                COALESCE(SUM(commission_earned), 0) as total_earned,
                COUNT(CASE WHEN DATE(clicked_at) = DATE('now') THEN 1 END) as clicks_today
            FROM affiliate_clicks 
            WHERE user_id = ?
        ''', (session['user_id'],))

        stats = cursor.fetchone()
        conn.close()

        return {
            'success': True,
            'total_clicks': stats[0],
            'total_conversions': stats[1], 
            'total_earned': stats[2],
            'clicks_today': stats[3],
            'conversion_rate': (stats[1] / stats[0] * 100) if stats[0] > 0 else 0
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/simulate_sale', methods=['POST'])
@login_required
def simulate_affiliate_sale():
    """Simulate an affiliate sale for demonstration"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        sale_amount = float(data.get('sale_amount', 25.99))
        commission_rate = float(data.get('commission_rate', 0.10))

        # Process the commission
        success = process_affiliate_commission(
            session['user_id'], 
            product_id, 
            sale_amount, 
            commission_rate
        )

        if success:
            commission_earned = sale_amount * commission_rate
            flash(f'🎉 Guul! Someone bought through your link! You earned ${commission_earned:.2f}!')
            return {'success': True, 'commission': commission_earned}
        else:
            return {'success': False, 'error': 'Commission processing failed'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/affiliate/advanced')
@login_required
def advanced_affiliate():
    """Advanced affiliate dashboard with real earnings tracking"""
    try:
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        # Get user's affiliate links and performance
        cursor.execute('''
            SELECT product_name, link_code, clicks, conversions, commission_rate
            FROM affiliate_links WHERE user_id = ?
        ''', (session['user_id'],))
        affiliate_links = cursor.fetchall()

        # Calculate total affiliate earnings
        cursor.execute('''
            SELECT SUM(amount) FROM transactions 
            WHERE user_id = ? AND type = 'earning' AND description LIKE '%affiliate%'
        ''', (session['user_id'],))
        total_affiliate_earnings = cursor.fetchone()[0] or 0

        # Get recent affiliate activity
        cursor.execute('''
            SELECT amount, description, created_at FROM transactions 
            WHERE user_id = ? AND type = 'earning' 
            ORDER BY created_at DESC LIMIT 10
        ''', (session['user_id'],))
        recent_earnings = cursor.fetchall()

        conn.close()

        return render_template('advanced_affiliate.html',
                             affiliate_links=affiliate_links,
                             total_affiliate_earnings=total_affiliate_earnings,
                             recent_earnings=recent_earnings)
    except Exception as e:
        flash('Khalad ayaa dhacay affiliate dashboard-ka.')
        return redirect(url_for('affiliate'))

@app.route('/create_affiliate_link', methods=['POST'])
@login_required
def create_affiliate_link():
    """Create new affiliate marketing link"""
    try:
        product_name = sanitize_input(request.form.get('product_name'))
        commission_rate = float(request.form.get('commission_rate', 0.20))

        if not product_name:
            flash('Fadlan geli magaca product-ka.')
            return redirect(url_for('advanced_affiliate'))

        # Generate unique link code
        link_code = f"AFF-{secrets.token_hex(8).upper()}"

        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO affiliate_links (user_id, product_name, link_code, commission_rate)
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], product_name, link_code, commission_rate))

        conn.commit()
        conn.close()

        flash(f'Affiliate link waa la sameeyay: {link_code}')
        return redirect(url_for('advanced_affiliate'))

    except Exception as e:
        flash('Khalad ayaa dhacay affiliate link samayniisa.')
        return redirect(url_for('advanced_affiliate'))

@app.route('/admin/toggle_user_status', methods=['POST'])
@admin_required
def toggle_user_status():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        new_status = data.get('status')

        if new_status not in ['active', 'suspended']:
            return {'success': False, 'error': 'Invalid status'}

        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        cursor.execute('UPDATE users SET status = ? WHERE id = ?', (new_status, user_id))
        conn.commit()
        conn.close()

        return {'success': True, 'message': f'User status updated to {new_status}'}

    except Exception as e:
        print(f"Toggle user status error: {e}")
        return {'success': False, 'error': str(e)}

@app.route('/admin/delete_user', methods=['POST'])
@admin_required
def delete_user():
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        # Delete user's transactions first (foreign key constraint)
        cursor.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM referrals WHERE referrer_id = ? OR referred_id = ?', (user_id, user_id))
        cursor.execute('DELETE FROM affiliate_links WHERE user_id = ?', (user_id,))

        # Delete the user
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))

        conn.commit()
        conn.close()

        return {'success': True, 'message': 'User deleted successfully'}

    except Exception as e:
        print(f"Delete user error: {e}")
        return {'success': False, 'error': str(e)}

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = sqlite3.connect('dadaal.db')
    cursor = conn.cursor()

    # Get all users with detailed information
    cursor.execute('''
        SELECT u.id, u.name, u.email, u.phone, u.total_earnings, u.status, 
               u.premium_until, u.created_at, u.referral_code,
               COUNT(r.id) as referrals_count
        FROM users u
        LEFT JOIN referrals r ON u.id = r.referrer_id AND r.status = 'completed'
        GROUP BY u.id
        ORDER BY u.created_at DESC
    ''')
    users = cursor.fetchall()

    conn.close()

    return render_template('admin_users.html', users=users)

@app.route('/admin/payments')
@admin_required
def admin_payments():
    """Admin payment analytics dashboard."""
    try:
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        # Calculate total revenue
        cursor.execute('SELECT SUM(amount) FROM transactions WHERE status = "completed"')
        total_revenue = cursor.fetchone()[0] or 0

        # Payment method statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as mobile_money_count,
                COALESCE(SUM(amount), 0) as mobile_money_total
            FROM transactions 
            WHERE description LIKE '%mobile_money%' OR description LIKE '%Mobile Money%'
        ''')
        mobile_money_stats = cursor.fetchone()

        cursor.execute('''
            SELECT 
                COUNT(*) as credit_card_count,
                COALESCE(SUM(amount), 0) as credit_card_total
            FROM transactions 
            WHERE description LIKE '%credit_card%' OR description LIKE '%Credit Card%' OR description LIKE '%Stripe%'
        ''')
        credit_card_stats = cursor.fetchone()

        cursor.execute('''
            SELECT 
                COUNT(*) as bank_transfer_count,
                COALESCE(SUM(amount), 0) as bank_transfer_total
            FROM transactions 
            WHERE description LIKE '%bank_transfer%' OR description LIKE '%Bank Transfer%'
        ''')
        bank_transfer_stats = cursor.fetchone()

        cursor.execute('''
            SELECT 
                COUNT(*) as premium_count,
                COALESCE(SUM(amount), 0) as premium_total
            FROM transactions 
            WHERE type = 'premium'
        ''')
        premium_stats = cursor.fetchone()

        # Recent payments
        cursor.execute('''
            SELECT t.id, t.amount, t.type, t.status, u.name, t.created_at
            FROM transactions t
            JOIN users u ON t.user_id = u.id
            WHERE t.status = 'completed'
            ORDER BY t.created_at DESC
            LIMIT 20
        ''')
        recent_payments = cursor.fetchall()

        conn.close()

        return render_template('admin_payments.html',
                               total_revenue=total_revenue,
                               mobile_money_count=mobile_money_stats[0],
                               mobile_money_total=mobile_money_stats[1],
                               credit_card_count=credit_card_stats[0],
                               credit_card_total=credit_card_stats[1],
                               bank_transfer_count=bank_transfer_stats[0],
                               bank_transfer_total=bank_transfer_stats[1],
                               premium_count=premium_stats[0],
                               premium_total=premium_stats[1],
                               recent_payments=recent_payments)

    except Exception as e:
        print(f"Admin payments error: {e}")
        flash(f"Error loading payment analytics: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Admin analytics dashboard."""
    try:
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        # Total users
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        # Active users
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "active"')
        active_users = cursor.fetchone()[0]

        # Total transactions
        cursor.execute('SELECT COUNT(*) FROM transactions')
        total_transactions = cursor.fetchone()[0]

        # Total earnings
        cursor.execute('SELECT SUM(amount) FROM transactions WHERE type = "earning"')
        total_earnings = cursor.fetchone()[0] or 0

        # Recent user activity
        cursor.execute('''
            SELECT u.name, ual.activity_type, ual.description, ual.created_at
            FROM user_activity_logs ual
            JOIN users u ON ual.user_id = u.id
            ORDER BY ual.created_at DESC
            LIMIT 10
        ''')
        recent_activity = cursor.fetchall()

        # Payment statistics
        cursor.execute('''
            SELECT type, COUNT(*), SUM(amount)
            FROM transactions
            WHERE type IN ('earning', 'withdrawal', 'referral', 'premium', 'bonus')
            GROUP BY type
        ''')
        payment_stats = cursor.fetchall()

        conn.close()

        return render_template('admin_analytics.html',
                               total_users=total_users,
                               active_users=active_users,
                               total_transactions=total_transactions,
                               total_earnings=total_earnings,
                               recent_activity=recent_activity,
                               payment_stats=payment_stats)

    except Exception as e:
        print(f"Analytics error: {e}")
        flash(f"Error loading analytics: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/earnings')
def earnings():
    return render_template('earnings.html', 
                         total_earnings=total_earnings,
                         affiliate_earnings=affiliate_earnings,
                         referral_count=len(user_referrals))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/ads.txt')
def ads_txt():
    return "google.com, pub-6630634320422572, DIRECT, f08c47fec0942fa0", 200, {'Content-Type': 'text/plain'}

@app.route('/robots.txt')
def robots_txt():
    return """User-agent: *
Allow: /
Sitemap: https://dadaal.onrender.com/sitemap.xml""", 200, {'Content-Type': 'text/plain'}

@app.route('/wholesale')
def wholesale():
    """Wholesale/Distributor program main page"""
    return render_template('wholesale.html')

@app.route('/wholesale_signup', methods=['POST'])
def wholesale_signup():
    """Handle wholesale partner signup"""
    try:
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = request.form.to_dict()

        # Extract form data
        company_name = sanitize_input(data.get('company_name'))
        contact_person = sanitize_input(data.get('contact_person'))
        business_email = sanitize_input(data.get('business_email'))
        business_phone = sanitize_input(data.get('business_phone'))
        website = sanitize_input(data.get('website', ''))
        business_type = sanitize_input(data.get('business_type'))
        product_category = sanitize_input(data.get('product_category'))
        business_description = sanitize_input(data.get('business_description'))
        monthly_volume = float(data.get('monthly_volume', 0))

        # Validation
        if not all([company_name, contact_person, business_email, business_type, product_category]):
            return {'success': False, 'error': 'Fadlan buuxi dhammaan qeybaha muhiimka ah'}

        if not validate_email(business_email):
            return {'success': False, 'error': 'Business email format khalad'}

        # Determine commission tier based on monthly volume
        if monthly_volume >= 10000:
            commission_tier = 'diamond'
        elif monthly_volume >= 5000:
            commission_tier = 'gold'
        elif monthly_volume >= 1000:
            commission_tier = 'silver'
        else:
            commission_tier = 'bronze'

        try:
            conn = sqlite3.connect('dadaal.db', timeout=20.0)
            conn.execute('PRAGMA journal_mode=WAL;')  # Better concurrency
            cursor = conn.cursor()

            # Check if business email already exists
            cursor.execute('SELECT id FROM wholesale_partners WHERE business_email = ?', (business_email,))
            existing_partner = cursor.fetchone()
            if existing_partner:
                conn.close()
                if request.content_type == 'application/json':
                    return {'success': False, 'error': 'Business email-kan horay ayaa loo isticmaalay wholesale partner ahaan'}
                else:
                    flash('Business email-kan horay ayaa loo isticmaalay wholesale partner ahaan.')
                    return redirect(url_for('wholesale'))
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                if request.content_type == 'application/json':
                    return {'success': False, 'error': 'Database waa xidhani hadda. Fadlan daqiiqo dhawr ka dib isku day.'}
                else:
                    flash('Database waa xidhani hadda. Fadlan daqiiqo dhawr ka dib isku day.')
                    return redirect(url_for('wholesale'))
            else:
                raise e

        # Get user_id from session (if logged in) or create guest application
        user_id = session.get('user_id')
        if not user_id:
            # Check if email already exists as a regular user
            cursor.execute('SELECT id FROM users WHERE email = ?', (business_email,))
            existing_user = cursor.fetchone()
            if existing_user:
                user_id = existing_user[0]
            else:
                # Create a temporary user for this application
                cursor.execute('''
                    INSERT INTO users (name, email, password_hash, status)
                    VALUES (?, ?, ?, 'wholesale_pending')
                ''', (contact_person, business_email, hash_password('temp_password')))
                user_id = cursor.lastrowid

        # Insert wholesale partner application
        cursor.execute('''
            INSERT INTO wholesale_partners (
                user_id, company_name, contact_person, business_email, 
                business_phone, website, business_type, product_category,
                business_description, monthly_volume, commission_tier
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, company_name, contact_person, business_email,
              business_phone, website, business_type, product_category,
              business_description, monthly_volume, commission_tier))

        partner_id = cursor.lastrowid

        conn.commit()

        # Send notification email to admin
        try:
            send_wholesale_notification(company_name, contact_person, business_email)
        except:
            pass  # Don't fail if email fails

        if request.content_type == 'application/json':
            return {'success': True, 'message': 'Application waa la gudbiyay si guul leh!', 'partner_id': partner_id}
        else:
            flash(f'Guul! Application waa la gudbiyay. Partner ID: WS-{partner_id:04d}. Waan kala soo xiriiri doonaa 24 saacadood gudahood.')
            return redirect(url_for('wholesale_dashboard'))

    except Exception as db_error:
        if 'conn' in locals():
            conn.rollback()
        print(f"Database error in wholesale signup: {db_error}")
        if request.content_type == 'application/json':
            return {'success': False, 'error': f'Database error: {str(db_error)}'}
        else:
            flash('Khalad ayaa dhacay application submit-ka. Fadlan isku day mar kale.')
            return redirect(url_for('wholesale'))
    finally:
        if 'conn' in locals():
            conn.close()

    except Exception as e:
        print(f"Wholesale signup error: {e}")
        if request.content_type == 'application/json':
            return {'success': False, 'error': f'Error: {str(e)}'}
        else:
            flash('Khalad ayaa dhacay application submit-ka.')
            return redirect(url_for('wholesale'))

@app.route('/wholesale/dashboard')
@login_required
def wholesale_dashboard():
    """Wholesale partner dashboard"""
    try:
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        # Get partner info
        cursor.execute('''
            SELECT * FROM wholesale_partners 
            WHERE user_id = ? 
            ORDER BY created_at DESC LIMIT 1
        ''', (session['user_id'],))
        partner_data = cursor.fetchone()

        if not partner_data:
            flash('Ma lihid wholesale partner account. Fadlan apply-ka.')
            return redirect(url_for('wholesale'))

        # Get partner's products
        cursor.execute('''
            SELECT * FROM wholesale_products 
            WHERE partner_id = ? 
            ORDER BY created_at DESC
        ''', (partner_data[0],))
        products = cursor.fetchall()

        # Get sales stats
        cursor.execute('''
            SELECT COUNT(*), SUM(total_amount), SUM(commission_amount)
            FROM wholesale_sales 
            WHERE partner_id = ?
        ''', (partner_data[0],))
        sales_stats = cursor.fetchone()

        # Get recent sales
        cursor.execute('''
            SELECT ws.*, wp.product_name, u.name as buyer_name
            FROM wholesale_sales ws
            JOIN wholesale_products wp ON ws.product_id = wp.id
            JOIN users u ON ws.buyer_id = u.id
            WHERE ws.partner_id = ?
            ORDER BY ws.sale_date DESC
            LIMIT 10
        ''', (partner_data[0],))
        recent_sales = cursor.fetchall()

        conn.close()

        return render_template('wholesale_dashboard.html',
                             partner_data=partner_data,
                             products=products,
                             sales_stats=sales_stats,
                             recent_sales=recent_sales)

    except Exception as e:
        flash('Khalad ayaa dhacay dashboard-ka.')
        return redirect(url_for('wholesale'))

@app.route('/wholesale/buy_product', methods=['POST'])
@login_required
def buy_wholesale_product():
    """Process product purchase and instant commission"""
    try:
        product_id = int(request.form.get('product_id'))
        quantity = int(request.form.get('quantity', 1))

        conn = sqlite3.connect('dadaal.db', timeout=20.0)
        cursor = conn.cursor()

        # Get product details
        cursor.execute('''
            SELECT wp.*, wpart.user_id as partner_user_id, wpart.commission_tier
            FROM wholesale_products wp
            JOIN wholesale_partners wpart ON wp.partner_id = wpart.id
            WHERE wp.id = ? AND wp.status = 'active'
        ''', (product_id,))
        product = cursor.fetchone()

        if not product:
            flash('Product-kan ma jiro ama ma shaqeeyo.')
            return redirect(url_for('marketplace'))

        # Calculate amounts
        unit_price = product[3]  # price column
        total_amount = unit_price * quantity
        commission_rate = product[7]  # commission_rate column
        commission_amount = total_amount * commission_rate

        # Insert sale record
        cursor.execute('''
            INSERT INTO wholesale_sales (
                product_id, partner_id, buyer_id, quantity, unit_price, 
                total_amount, commission_amount, commission_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (product_id, product[0], session['user_id'], quantity, unit_price,
              total_amount, commission_amount, commission_rate))

        # Add instant commission to partner
        cursor.execute('''
            UPDATE users SET total_earnings = total_earnings + ?
            WHERE id = ?
        ''', (commission_amount, product[-2]))  # partner_user_id

        # Add transaction record for partner
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, description, status)
            VALUES (?, ?, 'earning', ?, 'completed')
        ''', (product[-2], commission_amount, f'Wholesale sale commission - {product[1]}'))

        # Update product stock
        cursor.execute('''
            UPDATE wholesale_products SET stock_quantity = stock_quantity - ?
            WHERE id = ?
        ''', (quantity, product_id))

        conn.commit()
        conn.close()

        flash(f'Guul! Product waa la iibsaday. Partner-ka wuxuu helay ${commission_amount:.2f} commission!')
        return redirect(url_for('marketplace'))

    except Exception as e:
        flash('Khalad ayaa dhacay product iibashada.')
        print(f"Wholesale buy error: {e}")
        return redirect(url_for('marketplace'))

@app.route('/wholesale/add_product', methods=['POST'])
@login_required
def add_wholesale_product():
    """Add product to wholesale catalog"""
    try:
        # Get form data
        product_name = sanitize_input(request.form.get('product_name'))
        description = sanitize_input(request.form.get('description'))
        price = float(request.form.get('price'))
        wholesale_price = float(request.form.get('wholesale_price', price * 0.7))
        category = sanitize_input(request.form.get('category'))
        sku = sanitize_input(request.form.get('sku'))
        stock_quantity = int(request.form.get('stock_quantity', 0))

        if not all([product_name, price > 0, category]):
            flash('Fadlan buuxi dhammaan macluumaadka product-ka.')
            return redirect(url_for('wholesale_dashboard'))

        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()

        # Get partner ID
        cursor.execute('SELECT id FROM wholesale_partners WHERE user_id = ?', (session['user_id'],))
        partner = cursor.fetchone()

        if not partner:
            flash('Ma lihid wholesale partner account.')
            return redirect(url_for('wholesale'))

        # Generate SKU if not provided
        if not sku:
            sku = f"WS-{partner[0]}-{secrets.token_hex(4).upper()}"

        # Insert product
        cursor.execute('''
            INSERT INTO wholesale_products (
                partner_id, product_name, description, price, wholesale_price,
                category, sku, stock_quantity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (partner[0], product_name, description, price, wholesale_price,
              category, sku, stock_quantity))

        conn.commit()
        conn.close()

        flash(f'Product "{product_name}" waa la ku daray catalog-ga!')
        return redirect(url_for('wholesale_dashboard'))

    except Exception as e:
        flash('Khalad ayaa dhacay product-ka ku darista.')
        return redirect(url_for('wholesale_dashboard'))

def send_wholesale_notification(company_name, contact_person, business_email):
    """Send notification to admin about new wholesale application"""
    try:
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@dadaal.com')

        subject = f"New Wholesale Partner Application: {company_name}"
        body = f"""
        New wholesale partner application received:

        Company: {company_name}
        Contact: {contact_person}
        Email: {business_email}

        Please review the application in the admin dashboard.
        """

        # Use existing email system
        msg = MIMEMultipart()
        msg['From'] = os.environ.get('GMAIL_USER', 'noreply@dadaal.com')
        msg['To'] = admin_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        print(f"Wholesale notification: {subject}")
        return True

    except Exception as e:
        print(f"Failed to send wholesale notification: {e}")
        return False

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        # Save to database
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contact_messages (name, email, subject, message)
            VALUES (?, ?, ?, ?)
        ''', (name, email, subject, message))
        conn.commit()
        conn.close()

        flash('Fariintaada si guul leh ayaa loo diray! Waan kaa jawaabi doonaa dhaqso dhaqso.')
        return redirect(url_for('contact'))

    return render_template('contact.html')

if __name__ == '__main__':
    # Check if running in production
    is_production = os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT')

    try:
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=not is_production  # Disable debug in production
        )
    except OSError as e:
        if "Address already in use" in str(e):
            print("Port 5000 is busy. Trying port 5001...")
            app.run(
                host='0.0.0.0',
                port=5001,
                debug=not is_production
            )
        else:
            raise e