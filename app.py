from flask import Flask, render_template, request, redirect, url_for, abort
from datetime import datetime
import sqlite3
import pytz

app = Flask(__name__)

DATABASE = 'bbs.db'
TIMEZONE = pytz.timezone('Asia/Tokyo')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """データベースを初期化します。"""
    init_db()
    print('Initialized the database.')

@app.route('/')
def index():
    db = get_db()
    threads = db.execute('SELECT id, title, created_at FROM threads ORDER BY created_at DESC').fetchall()
    return render_template('index.html', threads=threads)

@app.route('/thread/<int:thread_id>')
def view_thread(thread_id):
    db = get_db()
    thread = db.execute('SELECT id, title, created_at FROM threads WHERE id = ?', (thread_id,)).fetchone()
    comments = db.execute('SELECT id, name, body, created_at FROM comments WHERE thread_id = ? ORDER BY created_at ASC', (thread_id,)).fetchall()
    if thread is None:
        abort(404)
    return render_template('thread.html', thread=thread, comments=comments)

@app.route('/new', methods=['GET', 'POST'])
def new_thread():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        now_utc = datetime.utcnow()
        now_jst = now_utc.astimezone(TIMEZONE)
        db = get_db()
        db.execute('INSERT INTO threads (title, created_at) VALUES (?, ?)', (title, now_jst))
        thread_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.execute('INSERT INTO comments (thread_id, name, body, created_at) VALUES (?, ?, ?, ?)', (thread_id, '名無し', body, now_jst))
        db.commit()
        return redirect(url_for('view_thread', thread_id=thread_id))
    return render_template('new.html')

@app.route('/thread/<int:thread_id>', methods=['POST'])
def add_comment(thread_id):
    name = request.form.get('name', '名無し') # デフォルトで「名無し」を設定
    body = request.form['body']
    now_utc = datetime.utcnow()
    now_jst = now_utc.astimezone(TIMEZONE)
    db = get_db()
    db.execute('INSERT INTO comments (thread_id, name, body, created_at) VALUES (?, ?, ?, ?)', (thread_id, name, body, now_jst))
    db.commit()
    return redirect(url_for('view_thread', thread_id=thread_id))

if __name__ == '__main__':
    app.run(debug=True)
