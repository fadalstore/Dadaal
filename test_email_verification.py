
import os
import sqlite3
from datetime import datetime, timedelta
from app import send_verification_email, generate_verification_code

def test_email_verification():
    """Test email verification system"""
    
    # Test data
    test_email = "test@example.com"
    
    print("🧪 Testing Email Verification System...")
    print(f"Test email: {test_email}")
    
    # Generate verification code
    verification_code = generate_verification_code()
    print(f"Generated code: {verification_code}")
    
    # Test sending email
    print("\n📧 Testing email sending...")
    result = send_verification_email(test_email, verification_code)
    
    if result:
        print("✅ Email sending successful!")
        print("Check your Gmail credentials in Secrets:")
        print(f"GMAIL_USER: {os.environ.get('GMAIL_USER', 'NOT_SET')}")
        print(f"GMAIL_APP_PASSWORD: {'SET' if os.environ.get('GMAIL_APP_PASSWORD') else 'NOT_SET'}")
    else:
        print("❌ Email sending failed!")
    
    # Test database operations
    print("\n💾 Testing database operations...")
    try:
        conn = sqlite3.connect('dadaal.db')
        cursor = conn.cursor()
        
        # Insert test verification code
        expires_at = datetime.now() + timedelta(minutes=10)
        cursor.execute('''
            INSERT INTO email_verification_codes (email, code, expires_at)
            VALUES (?, ?, ?)
        ''', (test_email, verification_code, expires_at))
        
        # Check if code exists
        cursor.execute('''
            SELECT id, email, code FROM email_verification_codes 
            WHERE email = ? AND code = ? AND expires_at > ?
        ''', (test_email, verification_code, datetime.now()))
        
        result = cursor.fetchone()
        if result:
            print("✅ Database operations successful!")
            print(f"Verification record ID: {result[0]}")
        else:
            print("❌ Database operations failed!")
        
        # Cleanup test data
        cursor.execute('DELETE FROM email_verification_codes WHERE email = ?', (test_email,))
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_email_verification()
