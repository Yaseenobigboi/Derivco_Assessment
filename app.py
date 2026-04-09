# this must be the main entry point - starts the Flask server and handles all routes

import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from db import init_db, DATABASE

app = Flask(__name__)
app.secret_key = 'mzansibuilds-secret-key'


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            error = 'Username already taken.'
        else:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, generate_password_hash(password)))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        conn.close()
    return render_template('register.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        error = 'Invalid username or password.'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/feed')
def feed():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    projects = conn.execute('''
        SELECT projects.*, users.username
        FROM projects
        JOIN users ON projects.user_id = users.id
        WHERE projects.completed = 0
        ORDER BY projects.id DESC
    ''').fetchall()
    conn.close()
    return render_template('feed.html', projects=projects)


@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    projects = conn.execute('SELECT * FROM projects WHERE user_id = ?', (session.get('user_id'),)).fetchall()
    conn.close()
    return render_template('dashboard.html', username=session.get('username'), projects=projects)


@app.route('/projects/create', methods=['GET', 'POST'])
def create_project():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        stage = request.form['stage']
        support_required = request.form['support_required']
        conn = sqlite3.connect(DATABASE)
        conn.execute(
            'INSERT INTO projects (user_id, title, description, stage, support_required) VALUES (?, ?, ?, ?, ?)',
            (session['user_id'], title, description, stage, support_required)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('create_project.html')


@app.route('/projects/<int:project_id>')
def project_detail(project_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    project = conn.execute('''
        SELECT projects.*, users.username
        FROM projects
        JOIN users ON projects.user_id = users.id
        WHERE projects.id = ?
    ''', (project_id,)).fetchone()
    conn.close()
    if project is None:
        return 'Project not found', 404
    return render_template('project_detail.html', project=project)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
