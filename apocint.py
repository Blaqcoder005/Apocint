from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
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

# Folder paths inside 'static'
UPLOAD_FOLDER = os.path.join('static', 'uploads')
IMAGE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'event_images')
BOOK_UPLOAD_FOLDER = os.path.join('static', 'books')

# Automatically create the folders if they don't exist
for folder in [UPLOAD_FOLDER, IMAGE_UPLOAD_FOLDER, BOOK_UPLOAD_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Flask config
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['IMAGE_UPLOAD_FOLDER'] = IMAGE_UPLOAD_FOLDER
app.config['BOOK_UPLOAD_FOLDER'] = BOOK_UPLOAD_FOLDER

# Allowed file types
ALLOWED_EXTENSIONS = {'mp3', 'mp4', 'pdf', 'wav'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

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

    # Get the latest sermon
    cursor.execute("SELECT * FROM sermons ORDER BY id DESC LIMIT 1")
    latest_sermon_row = cursor.fetchone()
    latest_sermon = None
    if latest_sermon_row:
        columns = [desc[0] for desc in cursor.description]
        latest_sermon = dict(zip(columns, latest_sermon_row))

    # Get the upcoming event
    cursor.execute("SELECT * FROM events ORDER BY event_date ASC LIMIT 1")
    upcoming_event_row = cursor.fetchone()
    upcoming_event = None
    if upcoming_event_row:
        columns = [desc[0] for desc in cursor.description]
        upcoming_event = dict(zip(columns, upcoming_event_row))
        # Keep event_date as datetime for template formatting
        # No conversion to string here

    cursor.close()
    conn.close()

    return render_template(
        'home.html',
        latest_sermon=latest_sermon,
        upcoming_event=upcoming_event
    )

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
    cursor.execute("SELECT title, filename, uploaded_at FROM sermons ORDER BY uploaded_at DESC")
    rows = cursor.fetchall()
    sermons = [{"title": row[0], "file_name": row[1], "uploaded_at": row[2]} for row in rows]
    cursor.close()
    conn.close()
    return render_template('sermon.html', sermon_files=sermons)

@app.route('/event')
def event():
   
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events ORDER BY event_date DESC")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    events = [dict(zip(columns, row)) for row in rows]

    cursor.close()
    conn.close()

    return render_template('events.html', events=events)

@app.route('/resources')
def resources():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books ORDER BY uploaded_at DESC")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    books = [dict(zip(columns, row)) for row in rows]
    cursor.close()
    conn.close()
    return render_template('resources.html', books=books)
# === Auth Routes ===
@app.route('/create-admin')
def create_admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    from werkzeug.security import generate_password_hash
    hash_pw = generate_password_hash("Apocint")
    cursor.execute("INSERT INTO admins (username, password_hash) VALUES (%s, %s)", ("Apocint", hash_pw))
    conn.commit()
    cursor.close()
    conn.close()
    return "Admin created!"

@app.route('/update-admin-password')
def update_admin_password():
    conn = get_db_connection()
    cursor = conn.cursor()
    from werkzeug.security import generate_password_hash
    hash_pw = generate_password_hash("Apocint")  # or any new password you want
    cursor.execute("UPDATE admins SET password_hash = %s WHERE username = %s", (hash_pw, "Apocint"))
    conn.commit()
    cursor.close()
    conn.close()
    return "Admin password updated!"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM admins WHERE username = %s", (username,))
        result = cursor.fetchone()


        if result:
            from werkzeug.security import check_password_hash
            match = check_password_hash(result[0], password)
            print("Password match:", match)
            if match:
                session['admin_logged_in'] = True
                return redirect('/dashboard')

        return "Invalid credentials", 401

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
        upload_folder = os.path.join('static', 'uploads')
        
        # ✅ Ensure the folder exists
        os.makedirs(upload_folder, exist_ok=True)

        filepath = os.path.join(upload_folder, filename)
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
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))

    title = request.form.get('title')
    book_file = request.files.get('book')

    if not title or not book_file:
        return "Missing title or book file", 400

    if not book_file.filename.lower().endswith('.pdf'):
        return "Invalid file type. Only PDFs allowed.", 400

    filename = secure_filename(book_file.filename)
    save_path = os.path.join(app.config['BOOK_UPLOAD_FOLDER'], filename)

    # Ensure the folder exists (just in case)
    os.makedirs(app.config['BOOK_UPLOAD_FOLDER'], exist_ok=True)

    try:
        book_file.save(save_path)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO books (title, filename) VALUES (%s, %s)",
            (title, filename)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for("admin_resources"))

    except Exception as e:
        return f"Error saving file: {str(e)}", 500

@app.route('/admin/delete-book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_name FROM books WHERE id = %s", (book_id,))
    result = cursor.fetchone()

    if result:
        file_path = os.path.join('static/books', result[0])
        if os.path.exists(file_path):
            os.remove(file_path)

        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        conn.commit()

    cursor.close()
    conn.close()
    return redirect(url_for("admin_resources"))

@app.route('/upload-event', methods=['POST'])
def upload_event():
    title = request.form.get("title")
    date = request.form.get("date")
    desc = request.form.get("description")
    image_file = request.files.get("event_image")

    if not title or not date or not desc:
        return "Missing form data", 400

    image_filename = None
    if image_file and image_file.filename:
        if allowed_image(image_file.filename):
            filename = secure_filename(image_file.filename)
            os.makedirs(app.config['IMAGE_UPLOAD_FOLDER'], exist_ok=True)
            image_path = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_filename = filename
        else:
            return "Invalid image file format", 400

    # Save event to DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (title, event_date, description, image_filename) VALUES (%s, %s, %s, %s)",
        (title, date, desc, image_filename)
    )
    conn.commit()
    conn.close()

    flash("Event added successfully!")
    return redirect(url_for('admin_events'))

# === Sermon Viewer ===
@app.route('/admin/sermons')
def admin_sermons():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, filename, uploaded_at FROM sermons ORDER BY uploaded_at DESC")
    rows = cursor.fetchall()
    sermons = [{"id": row[0], "title": row[1], "file_name": row[2], "uploaded_at": row[3]} for row in rows]
    cursor.close()
    conn.close()
    return render_template('admin_sermons.html', sermon_files=sermons)



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

@app.route('/admin/resources')
def admin_resources():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books ORDER BY uploaded_at DESC")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    books = [dict(zip(columns, row)) for row in rows]

    cursor.close()
    conn.close()

    return render_template('admin_resources.html', books=books)

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
