from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
from datetime import datetime
import os

# Import your abilities
from ability2_click_type import click_type_task
from ability3_find_elements import ability3_extract
from ability4_brain import think_and_plan
from ability5_browser import smart_browser_task
from ability6_formfill import form_fill_task
from ability7_universal_form import ability7_universal_form_task
from ability8_safe_submit import safe_submit_task
from ability9_textextract import extract_and_summarize
from ability10_research import research_task
from ability12_jobsearch import jobsearch_task
from ability13_career_agent import career_agent_task
from ability_shopping import shopping_assistant_task

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Database setup
def init_db():
    conn = sqlite3.connect('agent_system.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Tasks table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  task_description TEXT NOT NULL,
                  status TEXT DEFAULT 'pending',
                  result TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  completed_at TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # Profile data table
    c.execute('''CREATE TABLE IF NOT EXISTS profiles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER UNIQUE,
                  full_name TEXT,
                  email TEXT,
                  phone TEXT,
                  address TEXT,
                  linkedin_url TEXT,
                  resume_path TEXT,
                  skills TEXT,
                  city TEXT,
                  state TEXT,
                  pincode TEXT,
                  experience TEXT,
                  age INTEGER,
                  preferred_job_title TEXT,
                  preferred_location TEXT,
                  expected_salary TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    print("✅ Database tables created successfully!")
    
    conn.commit()
    conn.close()

init_db()

# Abilities configuration
ABILITIES = [
    {
        "id": 1,
        "name": "Form Filling",
        "description": "Automatically fill web forms with your data",
        "functions": ["Detect form fields", "Auto-fill data", "Universal compatibility"],
        "rating": 5,
        "status": "active"
    },
    {
        "id": 2,
        "name": "Deep Research",
        "description": "Conduct comprehensive web research on any topic",
        "functions": ["Search multiple sources", "Compile findings", "Generate reports"],
        "rating": 4,
        "status": "active"
    },
    {
        "id": 3,
        "name": "Smart Browser",
        "description": "Intelligent browser automation and navigation",
        "functions": ["Open websites", "Navigate pages", "Smart scrolling"],
        "rating": 5,
        "status": "active"
    },
    {
        "id": 4,
        "name": "AI Shopping Assistant",
        "description": "Find best deals across Amazon, Flipkart, Blinkit",
        "functions": ["Compare prices", "Find best deals", "Add to cart"],
        "rating": 5,
        "status": "active"
    },
    {
        "id": 5,
        "name": "AI Job Finder",
        "description": "Search jobs across multiple platforms based on your profile",
        "functions": ["Search multiple job portals", "Match based on profile", "Filter by salary & experience"],
        "rating": 5,
        "status": "active"
    },
    {
        "id": 6,
        "name": "AI Career Agent",
        "description": "Find internships on Internshala perfect for students",
        "functions": ["Search Internshala", "Filter by role & location", "Show TOP 3 matches"],
        "rating": 5,
        "status": "active"
    },
    {
        "id": 7,
        "name": "Auto Email Reply",
        "description": "Smart automated email responses",
        "functions": ["Read emails", "Generate replies", "Send responses"],
        "rating": 4,
        "status": "coming_soon"
    }
]

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        conn = sqlite3.connect('agent_system.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('agent_system.db')
            c = conn.cursor()
            c.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                     (username, email, hashed_password))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Account created successfully'})
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'message': 'Username or email already exists'})
    
    return render_template('signup.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', username=session.get('username'))

@app.route('/abilities')
def abilities():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('abilities.html', abilities=ABILITIES)

@app.route('/projects')
def projects():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('agent_system.db')
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC', 
              (session['user_id'],))
    tasks = c.fetchall()
    conn.close()
    
    return render_template('chat_history.html', tasks=tasks)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.json
        conn = sqlite3.connect('agent_system.db')
        c = conn.cursor()
        
        c.execute('''INSERT OR REPLACE INTO profiles 
                     (user_id, full_name, email, phone, address, linkedin_url, resume_path, skills, 
                      city, state, pincode, experience, age, preferred_job_title, preferred_location, expected_salary)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (session['user_id'], data.get('full_name'), data.get('email'),
                   data.get('phone'), data.get('address'), data.get('linkedin_url'),
                   data.get('resume_path'), data.get('skills'), data.get('city'),
                   data.get('state'), data.get('pincode'), data.get('experience'),
                   data.get('age'), data.get('preferred_job_title'), 
                   data.get('preferred_location'), data.get('expected_salary')))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Profile updated'})
    
    conn = sqlite3.connect('agent_system.db')
    c = conn.cursor()
    c.execute('SELECT * FROM profiles WHERE user_id = ?', (session['user_id'],))
    profile_data = c.fetchone()
    conn.close()
    
    return render_template('profile.html', profile=profile_data)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html', username=session.get('username'))

@app.route('/run-task', methods=['POST'])
def run_task():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    data = request.json
    task_description = data.get('task')
    
    # Save task to database
    conn = sqlite3.connect('agent_system.db')
    c = conn.cursor()
    c.execute('INSERT INTO tasks (user_id, task_description, status) VALUES (?, ?, ?)',
              (session['user_id'], task_description, 'running'))
    task_id = c.lastrowid
    conn.commit()
    
    # Get user profile for form filling
    c.execute('SELECT * FROM profiles WHERE user_id = ?', (session['user_id'],))
    profile = c.fetchone()
    conn.close()
    
    # Emit to websocket for real-time updates
    socketio.emit('task_started', {'task_id': task_id, 'description': task_description})
    
    try:
        # Use ability4_brain to decide which ability to use
        plan = think_and_plan(task_description)
        ability_chosen = plan.get('ability')
        
        socketio.emit('task_update', {'message': f'AI Brain chose: {ability_chosen}'})
        
        result = None
        
        # Route to the correct ability
        if ability_chosen == 'shopping':
            socketio.emit('task_update', {'message': '🛒 Starting AI Shopping Assistant...'})
            result = shopping_assistant_task(task_description, user_profile=profile)
        
        elif ability_chosen == 'jobsearch' or 'job' in task_description.lower():
            socketio.emit('task_update', {'message': '💼 Searching for jobs...'})
            result = jobsearch_task(task_description, user_profile=profile)
        
        elif ability_chosen == 'internship' or 'internship' in task_description.lower():
            socketio.emit('task_update', {'message': '🎓 Finding internships...'})
            result = career_agent_task(task_description, user_profile=profile)
        
        elif ability_chosen == 'ability2':
            socketio.emit('task_update', {'message': 'Running click & type...'})
            result = click_type_task(task_description)
        
        elif ability_chosen == 'ability3':
            socketio.emit('task_update', {'message': 'Extracting elements...'})
            result = ability3_extract(task_description)
        
        elif ability_chosen == 'ability5':
            socketio.emit('task_update', {'message': 'Opening browser...'})
            result = smart_browser_task(task_description)
        
        elif ability_chosen == 'ability6':
            socketio.emit('task_update', {'message': 'Filling form...'})
            result = form_fill_task(task_description)
        
        elif ability_chosen == 'ability7':
            socketio.emit('task_update', {'message': 'Universal form fill...'})
            result = ability7_universal_form_task(task_description)
        
        elif ability_chosen == 'ability9':
            socketio.emit('task_update', {'message': 'Extracting & summarizing...'})
            result = extract_and_summarize(task_description)
        
        elif ability_chosen == 'ability10':
            socketio.emit('task_update', {'message': 'Researching...'})
            result = research_task(task_description)
        
        else:
            result = {'status': 'error', 'message': 'No matching ability found'}
        
        # Update database with result
        conn = sqlite3.connect('agent_system.db')
        c = conn.cursor()
        c.execute('''UPDATE tasks 
                     SET status = ?, result = ?, completed_at = CURRENT_TIMESTAMP 
                     WHERE id = ?''',
                  ('completed', str(result), task_id))
        conn.commit()
        conn.close()
        
        socketio.emit('task_completed', {'task_id': task_id})
        socketio.emit('task_update', {'message': '✅ Task completed!'})
        
        return jsonify({'success': True, 'task_id': task_id, 'result': result})
    
    except Exception as e:
        # Handle errors
        conn = sqlite3.connect('agent_system.db')
        c = conn.cursor()
        c.execute('UPDATE tasks SET status = ?, result = ? WHERE id = ?',
                  ('failed', str(e), task_id))
        conn.commit()
        conn.close()
        
        socketio.emit('task_update', {'message': f'❌ Error: {str(e)}'})
        
        return jsonify({'success': False, 'error': str(e)})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
