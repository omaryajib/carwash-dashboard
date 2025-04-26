from flask import Flask, render_template, request, redirect, url_for, session, Response
from flask import redirect
import sqlite3
import os
import csv
import io
from functools import wraps

app = Flask(__name__)
app.secret_key = 'secret_key'

# Initialize DB with users
def init_db():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        # Wash table
        c.execute('''
            CREATE TABLE washes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                station TEXT,
                wash_type TEXT,
                water INTEGER,
                products TEXT,
                energy REAL
            )
        ''')
        # Users table
        c.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            )
        ''')
        # Default admin user
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ('admin', '1234', 'admin'))
        conn.commit()
        conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = username
            session['role'] = user[3]
            return redirect(url_for('dashboard'))
        return "Invalid credentials"
    return '''
    <form method="post">
        <input name="username" placeholder="Username">
        <input type="password" name="password" placeholder="Password">
        <input type="submit">
    </form>
    '''

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return redirect(url_for('login'))

# Add wash
@app.route('/add', methods=['POST'])
@login_required
def add():
    date = request.form['date']
    station = request.form['station']
    wash_type = request.form['wash_type']
    water = request.form['water']
    products = request.form['products']
    energy = request.form['energy']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO washes (date, station, wash_type, water, products, energy) VALUES (?, ?, ?, ?, ?, ?)",
              (date, station, wash_type, water, products, energy))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM washes")
    total_washes = c.fetchone()[0]

    c.execute("SELECT SUM(water) FROM washes")
    total_water = c.fetchone()[0] or 0

    c.execute("SELECT SUM(energy) FROM washes")
    total_energy = c.fetchone()[0] or 0

    c.execute("SELECT station, COUNT(*) FROM washes GROUP BY station ORDER BY COUNT(*) DESC LIMIT 1")
    top_station = c.fetchone()
    top_station = top_station[0] if top_station else "N/A"

    c.execute("SELECT station, COUNT(*) FROM washes GROUP BY station")
    station_data = dict(c.fetchall())

    c.execute("SELECT wash_type, COUNT(*) FROM washes GROUP BY wash_type")
    type_data = dict(c.fetchall())

    c.execute("SELECT * FROM washes ORDER BY id DESC")
    washes = c.fetchall()

    conn.close()

    return render_template('dashboard.html',
                           total_washes=total_washes,
                           total_water=total_water,
                           total_energy=total_energy,
                           top_station=top_station,
                           station_data=station_data,
                           type_data=type_data,
                           washes=washes)

# View records
@app.route('/records')
@login_required
def records():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM washes ORDER BY id DESC")
    washes = c.fetchall()
    conn.close()
    return render_template('records.html', washes=washes)

# Export CSV
@app.route('/export')
@login_required
def export_csv():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM washes")
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Date', 'Station', 'Type', 'Water (L)', 'Products', 'Energy (€)'])
    writer.writerows(rows)
    output.seek(0)

    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=washes.csv"}
    )

# Run app
if __name__ == '__main__':
    import os
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

@app.route('/')
def home():
    return redirect('/dashboard')

