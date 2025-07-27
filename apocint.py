from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from dotenv import load_dotenv
import os
from datetime import datetime
import time
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import session
from flask_login import login_user
import mysql.connector
from werkzeug.utils import secure_filename
import pg8000

load_dotenv(dotenv_path="/data/data/com.termux/files/home/Apocimt/apocint.env")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Dictionary to track failed login attempts
failed_logins = {}

# Constants
BLOCK_DURATION = 300  # seconds (5 minutes)
MAX_ATTEMPTS = 5

# Track failed login attempts
failed_logins = {}

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp3', 'mp4', 'pdf', 'wav'}

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSION

def get_db_connection():
    return pg8000.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )

# === Basic Public Pages ===
@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Latest sermon
    cursor.execute("SELECT * FROM sermons ORDER BY id DESC LIMIT 1")
    sermon_columns = [desc[0] for desc in cursor.description]
    latest_sermon = cursor.fetchone()
    latest_sermon = dict(zip(sermon_columns, latest_sermon)) if latest_sermon else None

    # Upcoming event
    cursor.execute("SELECT * FROM events ORDER BY event_date ASC LIMIT 1")
    event_columns = [desc[0] for desc in cursor.description]
    upcoming_event = cursor.fetchone()
    upcoming_event = dict(zip(event_columns, upcoming_event)) if upcoming_event else None

    cursor.close()
    conn.close()

    return render_template('home.html', latest_sermon=latest_sermon, upcoming_event=upcoming_event)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()

        if not name or not email or not message:
            return jsonify({'error': 'All fields are required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (name, email, message) VALUES (%s, %s, %s)",
            (name, email, message)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Message received successfully'}), 200

    return render_template('contact.html')

@app.route('/sermons')
def sermons():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sermons ORDER BY uploaded_at DESC")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    sermons = [dict(zip(columns, row)) for row in rows]

    cursor.close()
    conn.close()

    return render_template('sermon.html', sermon_files=sermons)

@app.route('/event')
def event():
   
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title, event_date, description FROM events ORDER BY event_date ASC")
    rows = cursor.fetchall()
    
    # Map to dictionary manually if dictionary=True didn't work
    events = []
    for row in rows:
        events.append({
            'title': row[0],
            'event_date': row[1],
            'description': row[2]
        })

    conn.close()
    return render_template('events.html', events=events)


# === Auth Routes ===
@app.route("/login", methods=["GET", "POST"])
def login():
    ip = request.remote_addr
    current_time = time.time()

    if request.method == "POST":
        failed_logins.setdefault(ip, [])
        failed_logins[ip] = [t for t in failed_logins[ip] if current_time - t < BLOCK_DURATION]

        if len(failed_logins[ip]) >= MAX_ATTEMPTS:
            return "Too many failed attempts. Try again later.", 429
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect('/dashboard')
        else:
            failed_logins[ip].append(current_time)
            return "Invalid credentials", 401
        print("USERNAME:", ADMIN_USERNAME)
        print("PASSWORD:", ADMIN_PASSWORD)

    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/login')
    return render_template('admin.html')

# === Upload Routes ===
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            with open('sermon_list.txt', 'a') as f:
                f.write(filename + '\n')

            flash('Sermon uploaded successfully.')
            return redirect(url_for('upload'))
        else:
            flash('No file selected.')
    return render_template('admin_uploads.html')

    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))

@app.route('/upload-sermon', methods=['POST'])
def upload_sermon():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))

    title = request.form['title']
    file = request.files['sermon_file']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sermons (title, filename) VALUES (%s, %s)", (title, filename))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Sermon uploaded successfully.")
    else:
        flash("Invalid file type.")

    return redirect(url_for('admin_upload'))

@app.route('/upload-book', methods=['POST'])
def upload_book():
    title = request.form['title']
    file = request.files['book_file']
    if file and allowed_file(file.filename, ['pdf']):
        filename = secure_filename(file.filename)
        file.save(os.path.join('static/books', filename))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO books (title, filename) VALUES (%s, %s)", (title, filename))
        conn.commit()
        conn.close()
        flash("Book uploaded!")
    return redirect(url_for('admin_upload'))

@app.route('/upload-event', methods=['POST'])
def upload_event():
    title = request.form.get("title")
    date = request.form.get("date")
    desc = request.form.get("description")

    print("Form values:", request.form)  # ✅ Leave this for debug

    if not title or not date or not desc:
        return "Missing form data", 400  # ❌ Defensive check

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (title, event_date, description) VALUES (%s, %s, %s)",
        (title, date, desc)
    )
    conn.commit()
    conn.close()

    flash("Event added successfully!")
    return redirect(url_for('admin_upload'))

# === Sermon Viewer ===
@app.route('/admin/sermons')
def admin_sermons():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sermons ORDER BY uploaded_at DESC")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    sermons = [dict(zip(columns, row)) for row in rows]

    cursor.close()
    conn.close()

    return render_template('admin_sermons.html', sermons=sermons)

@app.route('/delete/sermon/<int:sermon_id>', methods=['POST'])
def delete_sermon(sermon_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sermons WHERE id = %s", (sermon_id,))
    conn.commit()
    conn.close()
    flash('Sermon deleted.')
    return redirect(url_for('admin_sermons'))

# === Events (Public and Admin) ===
@app.route('/admin/events')
def admin_events():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM events ORDER BY event_date DESC")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    events = [dict(zip(columns, row)) for row in rows]

    cursor.close()
    conn.close()

    return render_template('admin_events.html', events=events)

@app.route('/delete/event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if 'admin_logged_in' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
    conn.commit()
    conn.close()
    flash("Event deleted successfully!")
    return redirect(url_for('admin_events'))

# === Admin Messages ===
@app.route('/admin/messages')
def admin_messages():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM messages ORDER BY created_at DESC")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    messages = [dict(zip(columns, row)) for row in rows]

    cursor.close()
    conn.close()

    return render_template('admin_messages.html', messages=messages)

@app.route('/admin/messages/delete/<int:message_id>', methods=['POST'])
def delete_message(message_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id = %s", (message_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('admin_messages'))

# === Upload Page Render ===
@app.route('/admin/upload')
def admin_upload():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('admin_uploads.html')

# === Database Test ===
@app.route('/test-db')
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        conn.close()
        return f"Connected! Tables: {[table[0] for table in tables]}"
    except Exception as e:
        return f"Database connection failed: {e}"

@app.route('/logout')
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))

# === Run Server ===
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=2000 , debug=True)
