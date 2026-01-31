from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import os
from urllib.parse import urlparse

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

# PostgreSQL connection - UPDATED FOR RENDER AUTO-CONNECTION
def get_db_connection():
    # Try DATABASE_URL first (Render's auto-generated), then INTELIX_DATABASE_URL
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('INTELIX_DATABASE_URL')
    
    if not database_url:
        raise ValueError("No database URL found! Make sure DATABASE_URL or INTELIX_DATABASE_URL is set in Render environment variables.")
    
    # Remove any whitespace
    database_url = database_url.strip()
    
    # Fix for Render's postgres:// URL format (psycopg2 needs postgresql://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print(f"🔗 Attempting to connect to database...") # Debug log
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        print("✅ Database connected successfully!") # Debug log
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        raise

# Database setup
def init_db():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Users table - UPDATED with subscription columns
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id SERIAL PRIMARY KEY,
                      username TEXT UNIQUE NOT NULL,
                      email TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL,
                      subscription TEXT DEFAULT 'free',
                      subscription_expires TIMESTAMP,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Tasks table
        c.execute('''CREATE TABLE IF NOT EXISTS tasks
                     (id SERIAL PRIMARY KEY,
                      user_id INTEGER,
                      task_description TEXT NOT NULL,
                      status TEXT DEFAULT 'pending',
                      result TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      completed_at TIMESTAMP,
                      FOREIGN KEY(user_id) REFERENCES users(id))''')
        
        # Profile data table
        c.execute('''CREATE TABLE IF NOT EXISTS profiles
                     (id SERIAL PRIMARY KEY,
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
        
        # Add subscription columns to existing users if they don't have them
        try:
            c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription TEXT DEFAULT 'free'")
            c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_expires TIMESTAMP")
        except:
            pass  # Columns already exist
        
        print("✅ Database tables created successfully!")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        raise

init_db()

# RATE LIMITING FUNCTION - NEW!
def check_user_limits(user_id):
    """Check if user has exceeded their monthly task limit"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get user subscription status
    c.execute('SELECT subscription FROM users WHERE id = %s', (user_id,))
    user = c.fetchone()
    subscription = user['subscription'] if user else 'free'
    
    # PRO users have unlimited tasks
    if subscription == 'pro':
        conn.close()
        return {'allowed': True, 'remaining': 'Unlimited', 'subscription': 'pro'}
    
    # Count tasks this month for FREE users
    first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    c.execute('''
        SELECT COUNT(*) as count 
        FROM tasks 
        WHERE user_id = %s 
        AND created_at >= %s
    ''', (user_id, first_day_of_month))
    
    result = c.fetchone()
    tasks_this_month = result['count'] if result else 0
    conn.close()
    
    # FREE tier limit: 10 tasks per month
    FREE_LIMIT = 10
    remaining = FREE_LIMIT - tasks_this_month
    
    return {
        'allowed': tasks_this_month < FREE_LIMIT,
        'remaining': max(0, remaining),
        'total': FREE_LIMIT,
        'used': tasks_this_month,
        'subscription': 'free'
    }

# Abilities configuration - UPDATED
ABILITIES = [
    {
        "id": 1,
        "name": "AI Shopping Assistant",
        "description": "Find best deals across Amazon, Flipkart, Blinkit",
        "functions": ["Compare prices", "Find best deals", "Add to cart"],
        "rating": 4,
        "status": "active"
    },
    {
        "id": 2,
        "name": "AI Job Finder",
        "description": "Search jobs across multiple platforms based on your profile",
        "functions": ["Search multiple job portals", "Match based on profile", "Filter by salary & experience"],
        "rating": 5,
        "status": "active"
    },
    {
        "id": 3,
        "name": "AI Career Agent",
        "description": "Find internships on Internshala perfect for students",
        "functions": ["Search Internshala", "Filter by role & location", "Show TOP 3 matches"],
        "rating": 5,
        "status": "active"
    },
    {
        "id": 4,
        "name": "Auto Email Reply",
        "description": "Smart automated email responses",
        "functions": ["Read emails", "Generate replies", "Send responses"],
        "rating": 4,
        "status": "coming_soon"
    },
    {
        "id": 5,
        "name": "AI Auto-Job Applier",
        "description": "Select jobs and auto-apply to multiple positions instantly",
        "functions": ["Select jobs to apply", "Auto-fill applications", "Submit to multiple portals"],
        "rating": 5,
        "status": "coming_soon",
        "badge": "pro_plan"
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
        
        print(f"🔐 Login attempt for user: {username}")
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = c.fetchone()
            conn.close()
            
            if not user:
                print(f"❌ User {username} not found")
                return jsonify({'success': False, 'message': 'Invalid credentials'})
            
            print(f"✅ User found, checking password...")
            
            if check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                print(f"✅ Login successful for {username}")
                return jsonify({'success': True, 'message': 'Login successful'})
            else:
                print(f"❌ Invalid password for {username}")
                return jsonify({'success': False, 'message': 'Invalid credentials'})
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Use method='pbkdf2:sha256' for consistent hashing
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('INSERT INTO users (username, email, password, subscription) VALUES (%s, %s, %s, %s)',
                     (username, email, hashed_password, 'free'))
            conn.commit()
            
            # Auto-login after signup
            c.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = c.fetchone()
            conn.close()
            
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                print(f"✅ User {username} created and logged in successfully!")
                return jsonify({'success': True, 'message': 'Account created successfully'})
            else:
                return jsonify({'success': False, 'message': 'Account created but login failed'})
                
        except psycopg2.IntegrityError as e:
            print(f"❌ Signup error: {str(e)}")
            return jsonify({'success': False, 'message': 'Username or email already exists'})
        except Exception as e:
            print(f"❌ Signup error: {str(e)}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    
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
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE user_id = %s ORDER BY created_at DESC', 
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
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''INSERT INTO profiles 
                     (user_id, full_name, email, phone, address, linkedin_url, resume_path, skills, 
                      city, state, pincode, experience, age, preferred_job_title, preferred_location, expected_salary)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                     ON CONFLICT (user_id) DO UPDATE SET
                     full_name = EXCLUDED.full_name,
                     email = EXCLUDED.email,
                     phone = EXCLUDED.phone,
                     address = EXCLUDED.address,
                     linkedin_url = EXCLUDED.linkedin_url,
                     resume_path = EXCLUDED.resume_path,
                     skills = EXCLUDED.skills,
                     city = EXCLUDED.city,
                     state = EXCLUDED.state,
                     pincode = EXCLUDED.pincode,
                     experience = EXCLUDED.experience,
                     age = EXCLUDED.age,
                     preferred_job_title = EXCLUDED.preferred_job_title,
                     preferred_location = EXCLUDED.preferred_location,
                     expected_salary = EXCLUDED.expected_salary''',
                  (session['user_id'], data.get('full_name'), data.get('email'),
                   data.get('phone'), data.get('address'), data.get('linkedin_url'),
                   data.get('resume_path'), data.get('skills'), data.get('city'),
                   data.get('state'), data.get('pincode'), data.get('experience'),
                   data.get('age'), data.get('preferred_job_title'), 
                   data.get('preferred_location'), data.get('expected_salary')))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Profile updated'})
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM profiles WHERE user_id = %s', (session['user_id'],))
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

# NEW ROUTE - Check task limits
@app.route('/check-limits')
def check_limits():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'})
    
    limit_check = check_user_limits(session['user_id'])
    return jsonify(limit_check)

# UPDATED ROUTE - Run task with rate limiting
@app.route('/run-task', methods=['POST'])
def run_task():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # CHECK RATE LIMIT FIRST - NEW!
    limit_check = check_user_limits(session['user_id'])
    
    if not limit_check['allowed']:
        return jsonify({
            'success': False,
            'message': f'Monthly limit reached! You\'ve used all {limit_check["total"]} free tasks this month. Upgrade to PRO for unlimited tasks!',
            'limit_exceeded': True,
            'subscription': limit_check['subscription']
        })
    
    data = request.json
    task_description = data.get('task')
    
    # Save task to database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO tasks (user_id, task_description, status) VALUES (%s, %s, %s) RETURNING id',
              (session['user_id'], task_description, 'running'))
    task_id = c.fetchone()['id']
    conn.commit()
    
    # Get user profile for form filling
    c.execute('SELECT * FROM profiles WHERE user_id = %s', (session['user_id'],))
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
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''UPDATE tasks 
                     SET status = %s, result = %s, completed_at = CURRENT_TIMESTAMP 
                     WHERE id = %s''',
                  ('completed', str(result), task_id))
        conn.commit()
        conn.close()
        
        socketio.emit('task_completed', {'task_id': task_id})
        socketio.emit('task_update', {'message': '✅ Task completed!'})
        
        return jsonify({'success': True, 'task_id': task_id, 'result': result})
    
    except Exception as e:
        # Handle errors
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE tasks SET status = %s, result = %s WHERE id = %s',
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
