from flask import Flask, render_template, request, redirect, url_for, session, send_file, Response
import sqlite3
import os
import csv
import io
from functools import wraps

app = Flask(__name__)
app.secret_key = 'secret_key'

# Initialize DB
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS washes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station TEXT,
            wash_type TEXT,
            water INTEGER,
            product TEXT,
            energy INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Create Users Table
def create_users_table():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Decorator for login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        username = request.form['username']
        password = request.form['password']
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['logged_in'] = True
            return redirect('/dashboard')
        else:
            return 'Invalid Credentials'
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect('/login')

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM washes')
    washes = c.fetchall()
    conn.close()
    return render_template('dashboard.html', washes=washes)

# Add new wash
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        station = request.form['station']
        wash_type = request.form['wash_type']
        water = request.form['water']
        products = ', '.join(request.form.getlist('product'))
        energy = request.form['energy']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO washes (station, wash_type, water, product, energy) VALUES (?, ?, ?, ?, ?)',
                  (station, wash_type, water, products, energy))
        conn.commit()
        conn.close()
        return redirect('/dashboard')
    return render_template('add.html')

# Export to CSV
@app.route('/export')
@login_required
def export_csv():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM washes')
    washes = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Station', 'Wash Type', 'Water', 'Products', 'Energy', 'Date'])
    writer.writerows(washes)

    output.seek(0)

    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=washes.csv"}
    )

# Home redirect to dashboard
@app.route('/')
def home():
    return redirect('/dashboard')

# Run app
if __name__ == '__main__':
    init_db()
    create_users_table()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
