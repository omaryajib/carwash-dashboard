from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secret_key'  # مهم للـ flash messages و session

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS washes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            station TEXT NOT NULL,
            wash_type TEXT NOT NULL,
            water INTEGER NOT NULL,
            products TEXT,
            energy REAL
        )
    ''')
    # Add default admin user if not exists
    c.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not c.fetchone():
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', 'admin'))
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = username
            flash('Welcome back!', 'success')
            return redirect('/dashboard')
        else:
            flash('Invalid Credentials', 'danger')
            return redirect('/login')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please login first!', 'warning')
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM washes')
    washes = c.fetchall()

    # Summary Calculations
    total_washes = len(washes)
    total_water = sum(wash[4] for wash in washes)
    total_energy = sum(wash[6] or 0 for wash in washes)
    stations = [wash[2] for wash in washes]
    wash_types = [wash[3] for wash in washes]

    # Prepare data for charts
    station_data = {}
    type_data = {}
    for station in stations:
        station_data[station] = station_data.get(station, 0) + 1
    for wtype in wash_types:
        type_data[wtype] = type_data.get(wtype, 0) + 1

    # Top station
    top_station = max(station_data, key=station_data.get) if station_data else "N/A"

    conn.close()
    return render_template('dashboard.html', washes=washes,
                           total_washes=total_washes,
                           total_water=total_water,
                           total_energy=total_energy,
                           top_station=top_station,
                           station_data=station_data,
                           type_data=type_data)

@app.route('/add', methods=['POST'])
def add_wash():
    if 'username' not in session:
        flash('Please login first!', 'warning')
        return redirect('/login')

    date = request.form['date']
    station = request.form['station']
    wash_type = request.form['wash_type']
    water = request.form['water']
    products = request.form['products']
    energy = request.form['energy']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO washes (date, station, wash_type, water, products, energy)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (date, station, wash_type, water, products, energy))
    conn.commit()
    conn.close()

    flash('Wash record added successfully!', 'success')
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect('/login')

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
