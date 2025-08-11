import unittest
import tempfile
import os
import sqlite3
from app import app, init_db, migrate_database

class DadaalTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test database"""
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.app = app.test_client()
        init_db()

    def tearDown(self):
        """Clean up test database"""
        os.close(self.db_fd)
        try:
            os.unlink(app.config['DATABASE'])
        except:
            pass

    def test_home_page(self):
        """Test home page loads"""
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)

    def test_login_page(self):
        """Test login page loads"""
        rv = self.app.get('/login')
        self.assertEqual(rv.status_code, 200)

    def test_register_page(self):
        """Test register page loads"""
        rv = self.app.get('/register')
        self.assertEqual(rv.status_code, 200)

    def test_admin_login_required(self):
        """Test admin pages require authentication"""
        rv = self.app.get('/admin/dashboard')
        self.assertEqual(rv.status_code, 302)  # Should redirect

    def test_dashboard_login_required(self):
        """Test dashboard requires login"""
        rv = self.app.get('/dashboard')
        self.assertEqual(rv.status_code, 302)  # Should redirect

if __name__ == '__main__':
    print("🧪 Starting Dadaal App Tests...")
    unittest.main()