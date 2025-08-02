
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

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dadaal_secret_key_2025_change_in_production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

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
        # Email configuration - you can use a service like SendGrid, Gmail, etc.
        # For demo purposes, we'll simulate sending
        reset_link = f"https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')}/reset_password/{reset_token}"
        
        # In production, you would actually send an email here
        # For now, we'll just print the reset link
        print(f"Password reset link for {email}: {reset_link}")
        
        # Simulate successful email sending
        return True
        
    except Exception as e:
        print(f"Email sending error: {e}")
        return False

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
    
    # Check if password_hash column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'password_hash' not in columns:
        # Add missing columns to users table
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN password_hash TEXT NOT NULL DEFAULT ""')
            cursor.execute('ALTER TABLE users ADD COLUMN total_earnings REAL DEFAULT 0')
            cursor.execute('ALTER TABLE users ADD COLUMN referral_code TEXT')
            cursor.execute('ALTER TABLE users ADD COLUMN referrer_id INTEGER')
            cursor.execute('ALTER TABLE users ADD COLUMN status TEXT DEFAULT "active"')
            cursor.execute('ALTER TABLE users ADD COLUMN premium_until DATE')
            cursor.execute('ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0')
            cursor.execute('ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            cursor.execute('ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            print("Database migration completed successfully!")
        except sqlite3.OperationalError as e:
            print(f"Migration error (might be normal): {e}")
    
    conn.commit()
    conn.close()

# Initialize database
init_db()
migrate_database()

# Global variables for tracking earnings
total_earnings = 0
user_referrals = {}
affiliate_earnings = 0

@app.route('/')
def home():
    return render_template('index.html', earnings=total_earnings)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        
        # Admin password - change this in production!
        if password == 'dadaal_admin_2025':
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
        
        # Calculate commission (5% of payment)
        commission = amount * 0.05
        
        # Save payment transaction to database
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()
        
        # Generate unique reference ID
        reference_id = f"PAY-{secrets.token_hex(8).upper()}"
        
        # Insert payment transaction
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, status, description, reference_id)
            VALUES (?, ?, 'earning', 'completed', ?, ?)
        ''', (session['user_id'], commission, f'Commission waxaa laga helay lacag shubasho ${amount} via {payment_method}', reference_id))
        
        # Update user's total earnings
        cursor.execute('''
            UPDATE users SET total_earnings = total_earnings + ?
            WHERE id = ?
        ''', (commission, session['user_id']))
        
        conn.commit()
        conn.close()
        
        # Update global earnings
        global total_earnings
        total_earnings += commission
        
        flash(f'Guul! Lacagtaada ${amount} si guul leh ayaa loo aqbalay. Commission ${commission:.2f} ayaa lagugu daray.')
        return redirect(url_for('thankyou'))
    
    return render_template('payment.html')


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
        
        # Check if email exists
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            flash('Email-kan horay ayaa loo isticmaalay.')
            conn.close()
            return redirect(url_for('register'))
        
        # Find referrer if referral code provided
        referrer_id = None
        if referral_code:
            cursor.execute('SELECT id FROM users WHERE referral_code = ?', (referral_code,))
            referrer = cursor.fetchone()
            if referrer:
                referrer_id = referrer[0]
        
        # Create user
        password_hash = hash_password(password)
        user_referral_code = f"DADAAL-{random.randint(10000, 99999)}"
        
        try:
            cursor.execute('''
                INSERT INTO users (name, email, phone, password_hash, referral_code, referrer_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, email, phone, password_hash, user_referral_code, referrer_id))
            
            user_id = cursor.lastrowid
            
            # Create referral record if applicable
            if referrer_id:
                cursor.execute('''
                    INSERT INTO referrals (referrer_id, referred_id, commission_earned)
                    VALUES (?, ?, ?)
                ''', (referrer_id, user_id, 5.00))
                
                # Add referral bonus to referrer
                cursor.execute('''
                    UPDATE users SET total_earnings = total_earnings + 5.00 
                    WHERE id = ?
                ''', (referrer_id,))
            
            conn.commit()
            
            # Set session
            session['user_id'] = user_id
            session['user_name'] = name
            session.permanent = True
            
            conn.close()
            
            flash('Akoonkaaga si guul leh ayaa loo sameeyay! Hadda waxaad gali kartaa dashboard-ka.')
            return redirect(url_for('login'))
            
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
        
        # Calculate premium duration
        if plan == 'monthly':
            premium_days = 30
        else:  # yearly
            premium_days = 365
        
        # Calculate premium expiry date
        premium_until = datetime.now() + timedelta(days=premium_days)
        
        # Update user's premium status
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()
        
        # Generate transaction reference
        reference_id = f"PREM-{secrets.token_hex(8).upper()}"
        
        # Insert premium transaction
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, status, description, reference_id)
            VALUES (?, ?, 'premium', 'completed', ?, ?)
        ''', (session['user_id'], amount, f'Premium subscription - {plan} plan', reference_id))
        
        # Update user's premium status
        cursor.execute('''
            UPDATE users SET premium_until = ?
            WHERE id = ?
        ''', (premium_until.date(), session['user_id']))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'Premium {plan} plan activated until {premium_until.strftime("%Y-%m-%d")}'}
        
    except Exception as e:
        print(f"Premium processing error: {e}")
        return {'success': False, 'error': 'Payment processing failed'}

@app.route('/affiliate')
def affiliate():
    return render_template('affiliate.html')

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
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    )
