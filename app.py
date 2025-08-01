
from flask import Flask, render_template, request, redirect, url_for
import os
import random
import string

app = Flask(__name__)

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
    return render_template('referral.html')

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

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    )
