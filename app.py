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
    if not session.get('user_id'):
        return redirect(url_for('login'))
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    projects = conn.execute('SELECT * FROM projects WHERE user_id = ?', (session.get('user_id'),)).fetchall()
    collab_requests = conn.execute('''
        SELECT collaboration_requests.*, users.username, projects.title
        FROM collaboration_requests
        JOIN users ON collaboration_requests.user_id = users.id
        JOIN projects ON collaboration_requests.project_id = projects.id
        WHERE projects.user_id = ?
    ''', (session.get('user_id'),)).fetchall()
    conn.close()
    return render_template('dashboard.html', username=session.get('username'), projects=projects, collab_requests=collab_requests)


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
    comments = conn.execute('''
        SELECT comments.*, users.username
        FROM comments
        JOIN users ON comments.user_id = users.id
        WHERE comments.project_id = ?
    ''', (project_id,)).fetchall()
    milestones = conn.execute(
        'SELECT * FROM milestones WHERE project_id = ?', (project_id,)
    ).fetchall()
    conn.close()
    if project is None:
        return 'Project not found', 404
    return render_template('project_detail.html', project=project, comments=comments, milestones=milestones)


@app.route('/projects/<int:project_id>/comment', methods=['POST'])
def add_comment(project_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    body = request.form['body']
    conn = sqlite3.connect(DATABASE)
    conn.execute(
        'INSERT INTO comments (project_id, user_id, body) VALUES (?, ?, ?)',
        (project_id, session['user_id'], body)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('project_detail', project_id=project_id))


@app.route('/projects/<int:project_id>/request-collaboration', methods=['POST'])
def request_collaboration(project_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    conn = sqlite3.connect(DATABASE)
    conn.execute(
        'INSERT INTO collaboration_requests (project_id, user_id) VALUES (?, ?)',
        (project_id, session['user_id'])
    )
    conn.commit()
    conn.close()
    return redirect(url_for('project_detail', project_id=project_id))


@app.route('/projects/<int:project_id>/add-milestone', methods=['POST'])
def add_milestone(project_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    description = request.form['description']
    conn = sqlite3.connect(DATABASE)
    conn.execute(
        'INSERT INTO milestones (project_id, description) VALUES (?, ?)',
        (project_id, description)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('project_detail', project_id=project_id))


@app.route('/projects/<int:project_id>/update-progress', methods=['POST'])
def update_progress(project_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    progress = int(request.form['progress'])
    if progress < 0 or progress > 100:
        progress = max(0, min(100, progress))
    conn = sqlite3.connect(DATABASE)
    conn.execute(
        'UPDATE projects SET progress = ? WHERE id = ?',
        (progress, project_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('project_detail', project_id=project_id))


@app.route('/projects/<int:project_id>/complete', methods=['POST'])
def complete_project(project_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    conn = sqlite3.connect(DATABASE)
    conn.execute(
        'UPDATE projects SET completed = 1, progress = 100 WHERE id = ?',
        (project_id,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('celebration_wall'))


@app.route('/celebration-wall')
def celebration_wall():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    projects = conn.execute('''
        SELECT projects.*, users.username
        FROM projects
        JOIN users ON projects.user_id = users.id
        WHERE projects.completed = 1
        ORDER BY projects.id DESC
    ''').fetchall()
    conn.close()
    return render_template('celebration_wall.html', projects=projects)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
