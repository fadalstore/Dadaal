
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_smtp():
    try:
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        gmail_user = os.environ.get('GMAIL_USER')
        gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
        
        print(f"Gmail User: {gmail_user}")
        print(f"Gmail Password Set: {'Yes' if gmail_password else 'No'}")
        
        if not gmail_user or not gmail_password:
            print("❌ Gmail credentials NOT configured properly!")
            print("\nKa samee:")
            print("1. Replit Secrets tab-ka fur")
            print("2. GMAIL_USER = your_email@gmail.com")
            print("3. GMAIL_APP_PASSWORD = 16-character app password")
            return False
        
        # Test SMTP connection
        print("\n🔄 Testing SMTP connection...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(gmail_user, gmail_password)
        
        # Send test email
        test_email = gmail_user  # Send to yourself
        
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = test_email
        msg['Subject'] = "Dadaal App - Email Test"
        
        body = """
        Salaan!
        
        Tani waa test email Dadaal App-ka.
        
        Haddii aad arki karto farriintan, email system-ku waa shaqeynayaa!
        
        Test code: 123456
        
        Mahadsanid,
        Dadaal App
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        text = msg.as_string()
        server.sendmail(gmail_user, test_email, text)
        server.quit()
        
        print("✅ Test email SUCCESSFULLY sent!")
        print(f"📧 Check your email: {test_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email test FAILED: {e}")
        return False

if __name__ == "__main__":
    test_gmail_smtp()
