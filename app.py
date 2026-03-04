import os
from flask import Flask, render_template, g, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import cloudinary
import cloudinary.uploader

load_dotenv()

cloudinary.config(
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key = os.getenv('CLOUDINARY_API_KEY'),
    api_secret = os.getenv('CLOUDINARY_API_SECRET'),
    secure = True
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
socketio = SocketIO(app)

def format_date(dt):
    if not dt:
        return ""
        
    now = datetime.now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    msg_date = dt.date()

    time_str = dt.strftime('%H:%M')

    if msg_date == today:
        return time_str
    elif msg_date == yesterday:
        return f"Yesterday {time_str}"
    else:
        return dt.strftime('%d %b %H:%M')

@app.template_filter('human_date')
def human_date_filter(dt):
    return format_date(dt)

pool = ConnectionPool(
    conninfo=os.getenv('DATABASE_URL'),
    min_size=4,
    max_size=10,
    kwargs={"row_factory": dict_row}
)

def get_db():
    if 'db' not in g:
        g.db = pool.getconn()
    return g.db

@app.teardown_appcontext
def close_conn(e):
    db = g.pop('db', None)
    if db is not None:
        pool.putconn(db)

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            g.user = cur.fetchone()

@app.route('/')
def index():
    conn = get_db()

    messages = []
    if g.user:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT m.id, m.content, m.created_at, m.user_id, u.username, u.profile_image
                FROM messages m
                JOIN users u ON m.user_id = u.id
                ORDER BY m.created_at ASC
            """)
            messages = cur.fetchall()

    return render_template('index.html', messages=messages)

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        error = None

        if not username:
            error = 'Required user.'
        elif not password:
            error = 'Required password.'

        if error is None:
            try:
                with conn.cursor() as cur:
                    hashed_pw = generate_password_hash(password)
                    cur.execute(
                        "INSERT INTO users (username, password) VALUES (%s, %s)",
                        (username, hashed_pw)
                    )
                    conn.commit()
                return redirect(url_for('login'))
            except Exception as e:
                error = 'User already exists or an error occurred.'

        flash(error, 'danger')

    return render_template('auth/register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        error = None
        
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()

        if user is None or not check_password_hash(user['password'], password):
            error = 'Incorrect username or password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(url_for('index'))

        flash(error, 'danger')

    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not g.user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        try:
            upload_result = cloudinary.uploader.upload(file, folder="avatars")
            new_url = upload_result['secure_url']
            conn = get_db()
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET profile_image = %s WHERE id = %s", (new_url, session['user_id']))
                conn.commit()
            
            flash('Profile image updated!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            flash(f'Error uploading: {e}', 'danger')

    return render_template('profile.html')

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if not g.user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        error = None

        if not old_password or not new_password or not confirm_password:
            error = 'All fields are required.'
        elif new_password != confirm_password:
            error = 'New passwords do not match.'
        
        if error is None:
            conn = get_db()
            with conn.cursor() as cur:
                cur.execute("SELECT password FROM users WHERE id = %s", (session['user_id'],))
                user = cur.fetchone()
                
                if not user or not check_password_hash(user['password'], old_password):
                    error = 'Incorrect old password.'
                else:
                    hashed_pw = generate_password_hash(new_password)
                    cur.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_pw, session['user_id']))
                    conn.commit()
                    flash('Password changed successfully!', 'success')
                    return redirect(url_for('index'))
        
        if error:
            flash(error, 'danger')

    return render_template('change_password.html')

@socketio.on('connect')
def handle_connect():
    user_id = session.get('user_id')
    print(f'Client connected: {user_id}')

@socketio.on('disconnect')
def handle_disconnect():
    user_id = session.get('user_id')
    print(f'Client disconnected: {user_id}')

@socketio.on('message')
def handle_message(data):
    user_id = session.get('user_id')
    if not user_id:
        return

    content = data['content']
    conn = get_db()
    
    with conn.cursor() as cur:
        cur.execute("SELECT username, profile_image FROM users WHERE id = %s", (user_id,))
        user_data = cur.fetchone()
        username = user_data['username']
        profile_image = user_data['profile_image']
        cur.execute("INSERT INTO messages (user_id, content) VALUES (%s, %s) RETURNING id, created_at", (user_id, content))
        row = cur.fetchone()
        conn.commit()
        
        emit('message', {
            'id': row['id'],
            'user_id': user_id,
            'username': username, 
            'profile_image': profile_image,
            'content': content, 
            'timestamp': format_date(row['created_at'])
        }, broadcast=True)

@socketio.on('delete_message')
def handle_delete_message(data):
    message_id = data['message_id']
    user_role = session.get('role')
    user_id = session.get('user_id')
    conn = get_db()
    
    with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM messages WHERE id = %s", (message_id,))
        msg = cur.fetchone()
        if not msg:
            return
        if user_role == 'admin' or msg['user_id'] == user_id:
            cur.execute("DELETE FROM messages WHERE id = %s", (message_id,))
            emit('message_deleted', {'id': message_id}, broadcast=True)
            conn.commit()
        else:
            emit('error', {'message': 'Do not have permission to delete messages.'})

@socketio.on('update_message')
def handle_update_message(data):
    message_id = data['message_id']
    new_content = data['new_content']
    user_id = session.get('user_id')
    conn = get_db()
    
    with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM messages WHERE id = %s", (message_id,))
        msg = cur.fetchone()
        
        if not msg:
            return
            
        if msg['user_id'] == user_id:
            cur.execute("UPDATE messages SET content = %s WHERE id = %s", (new_content, message_id))
            emit('message_edited', {'id': message_id, 'content': new_content}, broadcast=True)
            conn.commit()
        else:
            emit('error', {'message': 'Do not have permission to delete messages.'})
               
    

if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0', port=5000)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
