from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import os
from datetime import datetime
import time
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import session
from flask_login import login_user

load_dotenv(dotenv_path="/data/data/com.termux/files/home/Apocimt/apocint.env")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")



UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    return mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "Blacknigga05",
        database = "Apocint"
      )


@app.route("/")
def index():
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    username = request.form.get('username')
    password = request.form.get('password')

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return redirect('/dashboard')
    else:
        failed_logins[ip].append(current_time)
        return "Invalid credentials", 401


@app.route('/dashboard')
def home():
    if not session.get('admin_logged_in'):
        return redirect('/')
    return render_template('admin.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Store filename in a text file
            with open('sermon_list.txt', 'a') as f:
                f.write(filename + '\n')

            flash('Sermon uploaded successfully.')
            return redirect(url_for('upload'))
        else:
            flash('No file selected.')
    return render_template('upload.html')

    if 'admin' not in session:
        return redirect(url_for('login'))  # redirect to login if not admin
    # ... rest of the code

@app.route('/contact', methods=['POST'])
def contact():
    data = request.get_json()
    name = data.get('name').strip()
    email = data.get('email').strip()
    message = data.get('message').strip()

    if not name or not email or not message:
       return jsonify({'error':'All field are required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages(name,email,message)VALUES(%s,%s,%s)",
        (name,email,message)
    )
    conn.commit()
    cursor.close()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Message received successfully'}), 200

@app.route('/sermons')
def sermons():
    sermon_files = []
    if os.path.exists('sermon_list.txt'):
        with open('sermon_list.txt', 'r') as f:
            sermon_files = [line.strip() for line in f if line.strip()]
    return render_template('sermons.html', sermon_files=sermon_files)

@app.route('/admin/messages')
def admin_messages():
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT*FROM messages ORDER BY data_sent DESC")
    messages = cursor.fetchall()
    conn.close()

    return render_template('admin_messages.html')

@app.route('/admin/messages/delete/<int:message_id>', methods=['POST'])
def delete_message(message_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id = %s", (message_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('get_messages'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=2000, debug=True)
