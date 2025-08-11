
import unittest
import tempfile
import os
import sqlite3
from app import app, init_db, migrate_database

class DadaalAppTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.app = app.test_client()
        
        # Initialize test database
        with app.app_context():
            init_db()
            migrate_database()
    
    def tearDown(self):
        """Clean up after tests"""
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
    
    def test_home_page(self):
        """Test home page loads correctly"""
        rv = self.app.get('/')
        assert b'Dadaal' in rv.data
        assert rv.status_code == 200
    
    def test_register_page(self):
        """Test registration page loads"""
        rv = self.app.get('/register')
        assert rv.status_code == 200
        assert b'register' in rv.data
    
    def test_login_page(self):
        """Test login page loads"""
        rv = self.app.get('/login')
        assert rv.status_code == 200
        assert b'login' in rv.data
    
    def test_dashboard_without_login(self):
        """Test dashboard redirects when not logged in"""
        rv = self.app.get('/dashboard', follow_redirects=True)
        assert b'login' in rv.data
    
    def test_email_validation(self):
        """Test email validation function"""
        from app import validate_email
        
        # Valid emails
        assert validate_email('test@example.com') == True
        assert validate_email('user@gmail.com') == True
        
        # Invalid emails
        assert validate_email('invalid-email') == False
        assert validate_email('test@') == False
        assert validate_email('@example.com') == False
    
    def test_phone_validation(self):
        """Test phone validation function"""
        from app import validate_phone
        
        # Valid phones
        assert validate_phone('+252611234567') == True
        assert validate_phone('252611234567') == True
        
        # Invalid phones
        assert validate_phone('123') == False
        assert validate_phone('abc') == False

if __name__ == '__main__':
    print("🧪 Starting Dadaal App Tests...")
    unittest.main()
