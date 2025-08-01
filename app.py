
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'dadaal_secret_key'

# Database setup
def init_db():
    conn = sqlite3.connect('dadaal.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS topups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount INTEGER NOT NULL,
        bonus INTEGER NOT NULL,
        total INTEGER NOT NULL
    )""")
    conn.commit()
    conn.close()

# Fibonacci logic
def is_fibonacci(n):
    a, b = 0, 1
    while b < n:
        a, b = b, a + b
    return b == n

def next_fibonacci(n):
    a, b = 0, 1
    while b <= n:
        a, b = b, a + b
    return b

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        try:
            amount = int(request.form['amount'])
            if is_fibonacci(amount):
                bonus = next_fibonacci(amount)
                total = amount + bonus

                conn = sqlite3.connect('dadaal.db')
                c = conn.cursor()
                c.execute("INSERT INTO topups (amount, bonus, total) VALUES (?, ?, ?)", (amount, bonus, total))
                conn.commit()
                conn.close()

                result = {
                    'amount': amount,
                    'bonus': bonus,
                    'total': total,
                    'success': True
                }
            else:
                result = {'success': False}
        except:
            result = {'success': False}
    return render_template('index.html', result=result)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == 'Fadal835':
            session['admin'] = True
            return redirect(url_for('dashboard'))
    return render_template('admin.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    conn = sqlite3.connect('dadaal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM topups ORDER BY id DESC")
    data = c.fetchall()
    conn.close()
    return render_template('dashboard.html', data=data)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
