from flask import Flask, render_template, request, redirect, session, Response
import sqlite3
import os
import csv
import io
from functools import wraps

app = Flask(__name__)
app.secret_key = 'secret_key'

# Initialize DB with users
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Ajouter utilisateur test si la table est vide
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', 'admin'))
    conn.commit()
    conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# Home redirects to dashboard
@app.route('/')
def home():
    return redirect('/dashboard')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['logged_in'] = True
            return redirect('/dashboard')
        else:
            return "Invalid Credentials"
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Users list route
@app.route('/users')
@login_required
def users():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, password FROM users')
    users_list = cursor.fetchall()
    conn.close()
    output = '<h1>All Users</h1><ul>'
    for user in users_list:
        output += f'<li>Username: {user[0]}, Password: {user[1]}</li>'
    output += '</ul>'
    return output

# Export CSV
@app.route('/export_csv')
@login_required
def export_csv():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, password FROM users')
    data = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Username', 'Password'])
    writer.writerows(data)
    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=users.csv"}
    )

# Run app
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
@app.route('/add', methods=['POST'])
def add_wash():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    date = request.form['date']
    station = request.form['station']
    wash_type = request.form['wash_type']
    water = request.form['water']
    products = request.form['products']
    energy = request.form['energy']
    cursor.execute('''
        INSERT INTO washes (date, station, wash_type, water, products, energy)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (date, station, wash_type, water, products, energy))
    conn.commit()
    conn.close()
    return redirect('/dashboard')
