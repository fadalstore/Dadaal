
from flask import Flask, render_template, request, redirect, url_for, flash
import os
import random
import string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'dadaal_secret_key_2025'

# Database setup
def init_db():
    conn = sqlite3.connect('dadaal.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            total_earnings REAL DEFAULT 0,
            referral_code TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Global variables for tracking earnings
total_earnings = 0
user_referrals = {}
affiliate_earnings = 0

@app.route('/')
def home():
    return render_template('index.html', earnings=total_earnings)

@app.route('/admin')
def admin():
    return render_template('admin.html', total_earnings=total_earnings, affiliate_earnings=affiliate_earnings)

@app.route('/dashboard')
def dashboard():
    # Test data for now
    data = [
        [1, 100, 10, 110],
        [2, 200, 20, 220],
        [3, 150, 15, 165]
    ]
    return render_template('dashboard.html', data=data, earnings=total_earnings)

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        global total_earnings
        total_earnings += amount * 0.05  # 5% commission
        return redirect(url_for('thankyou'))
    return render_template('payment.html')

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

@app.route('/premium')
def premium():
    return render_template('premium.html')

@app.route('/affiliate')
def affiliate():
    return render_template('affiliate.html')

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
