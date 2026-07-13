import os
import sqlite3
import threading
from functools import wraps
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from hermes import HawkscanAgent
from scheduler import run_analysis_job

load_dotenv()

DATABASE = "users.db"
SCAN_TASKS = {}

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            target_competitors TEXT,
            is_admin BOOLEAN DEFAULT 0,
            total_tokens_used INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            error_message TEXT,
            endpoint TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trackers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            company_name TEXT NOT NULL,
            platform TEXT NOT NULL,
            baseline_price REAL,
            last_price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Run migrations
    try:
        cursor.execute("ALTER TABLE trackers ADD COLUMN last_market_high_url TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        cursor.execute("ALTER TABLE trackers ADD COLUMN last_market_low_url TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE scan_history ADD COLUMN market_high_url TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE scan_history ADD COLUMN market_low_url TEXT")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Initialize Hawkscan Agent
agent = HawkscanAgent()

# --- Decorators for Route Protection ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized. Please log in."}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            from werkzeug.exceptions import NotFound
            raise NotFound()  # Return 404 instead of 403 to keep it secretive
        return f(*args, **kwargs)
    return decorated_function

# --- Routes for HTML Pages ---

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('products.html')
import secrets
from datetime import datetime, timedelta

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash("Please enter your email.")
            return render_template('forgot_password.html')
            
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            user_id = user[0]
            token = secrets.token_urlsafe(32)
            cursor.execute("INSERT INTO password_resets (user_id, token) VALUES (?, ?)", (user_id, token))
            conn.commit()
            
            reset_link = url_for('reset_password', token=token, _external=True)
            
            try:
                from emailer import send_password_reset_email
                success = send_password_reset_email(email, reset_link)
                if not success:
                    flash("Email not configured. Here is your reset link (DEV MODE): " + reset_link)
            except Exception as e:
                flash("Error sending email: " + str(e))
                
        conn.close()
        flash("If that email exists, a reset link has been sent.")
        return redirect(url_for('login'))
        
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Clean up old tokens (> 1 hour)
    cursor.execute("DELETE FROM password_resets WHERE created_at < datetime('now', '-1 hour')")
    conn.commit()
    
    cursor.execute("SELECT user_id FROM password_resets WHERE token = ?", (token,))
    reset_record = cursor.fetchone()
    
    if not reset_record:
        conn.close()
        flash("Invalid or expired reset token.")
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        new_password = request.form.get('password')
        if not new_password or len(new_password) < 6:
            flash("Password must be at least 6 characters.")
            conn.close()
            return render_template('reset_password.html', token=token)
            
        hashed_pw = generate_password_hash(new_password)
        user_id = reset_record[0]
        
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, user_id))
        cursor.execute("DELETE FROM password_resets WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        
        flash("Your password has been reset! Please login.")
        return redirect(url_for('login'))
        
    conn.close()
    return render_template('reset_password.html', token=token)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash("Email and Password are required.")
            return render_template('login.html')
            
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, is_admin FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['is_admin'] = bool(user[2])
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.")
            return render_template('login.html')
            
    return render_template('login.html')

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash("Email and Password are required.")
            return render_template('sign-up.html')
            
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                flash("Email address already registered.")
                return render_template('sign-up.html')
            
            hashed_pw = generate_password_hash(password)
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_pw))
            conn.commit()
            
            # Fetch new user ID
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            new_user = cursor.fetchone()
            session['user_id'] = new_user[0]
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f"An error occurred: {e}")
        finally:
            conn.close()
            
    return render_template('sign-up.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))

@app.route('/pricing')
@login_required
def pricing():
    return render_template('pricing.html')

@app.route('/empty')
@login_required
def empty():
    return render_template('empty.html')

@app.route('/settings')
@login_required
def settings():
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT email, target_competitors FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return redirect(url_for('logout'))
        
    user_email = user[0]
    current_competitors = user[1] or ''
    return render_template('settings.html', user_email=user_email, current_competitors=current_competitors)

@app.route('/api/settings/password', methods=['POST'])
@login_required
def api_settings_password():
    new_password = request.form.get('new_password')
    if not new_password or len(new_password) < 6:
        flash("Password must be at least 6 characters.")
        return redirect(url_for('settings'))
        
    user_id = session['user_id']
    hashed_pw = generate_password_hash(new_password)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, user_id))
    conn.commit()
    conn.close()
    
    flash("Password updated successfully!")
    return redirect(url_for('settings'))

@app.route('/history')
@login_required
def history():
    return render_template('history.html')

@app.route('/chat')
@login_required
def chat_view():
    return render_template('chat.html')

@app.route('/api/analyze', methods=['POST'])
@login_required_api
def api_analyze():
    data = request.json
    product_name = data.get('product_name', '')
    company_name = data.get('company_name', '')
    platform = data.get('platform', '')
    
    user_id = session.get('user_id')
    
    if not product_name or not company_name or not platform:
        return jsonify({"error": "Product Name, Company Name, and Platform are required."}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, catalog_url FROM trackers WHERE user_id = ? AND product_name = ? AND company_name = ? AND platform = ?", 
                  (user_id, product_name, company_name, platform))
    row = cursor.fetchone()
    tracker_id = row[0] if row else None
    catalog_url = row[1] if row else None
    
    cursor.execute("SELECT target_competitors FROM users WHERE id = ?", (user_id,))
    comp_row = cursor.fetchone()
    conn.close()
    
    target_competitors = comp_row[0] if comp_row and comp_row[0] else None

    try:
        results = agent.analyze_prices(product_name, company_name, platform, catalog_url=catalog_url, target_competitors=target_competitors)
    except Exception as e:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO error_logs (user_id, error_message, endpoint) VALUES (?, ?, ?)", (user_id, str(e), "/api/analyze"))
        conn.commit()
        conn.close()
        return jsonify({"error": f"Scan failed: {str(e)}"}), 500

    results['catalog_url'] = catalog_url
    
    tokens_used = results.get('tokens_used', 0)
    
    if tracker_id and 'stats' in results:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        my_price = results.get('my_price')
        if my_price == "Not Found":
            my_price = None

        stats = results['stats']
        avg = stats.get('avg')
        high = stats.get('max')
        low = stats.get('min')
        min_url = stats.get('min_url')
        max_url = stats.get('max_url')
        
        # Insert into scan_history
        cursor.execute('''INSERT INTO scan_history (tracker_id, my_price, market_avg, market_high, market_low, market_high_url, market_low_url) 
                          VALUES (?, ?, ?, ?, ?, ?, ?)''', (tracker_id, my_price, avg, high, low, max_url, min_url))
        
        if my_price != "Error":
            # Update trackers table only if not an error
            cursor.execute('''UPDATE trackers 
                              SET last_price = ?, last_market_avg = ?, last_market_high = ?, last_market_low = ?, 
                                  last_market_high_url = ?, last_market_low_url = ?,
                                  scan_count = scan_count + 1, updated_at = CURRENT_TIMESTAMP 
                              WHERE id = ?''', (my_price, avg, high, low, max_url, min_url, tracker_id))
        else:
            # Just update scan count and timestamp if error
            cursor.execute('''UPDATE trackers 
                              SET scan_count = scan_count + 1, updated_at = CURRENT_TIMESTAMP 
                              WHERE id = ?''', (tracker_id,))
        
        if tokens_used > 0:
            cursor.execute("UPDATE users SET total_tokens_used = total_tokens_used + ? WHERE id = ?", (tokens_used, user_id))
            
        conn.commit()
        conn.close()
        
    return jsonify(results)

import time

def background_scan(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, product_name, company_name, platform, catalog_url FROM trackers WHERE user_id = ? AND is_active = 1", (user_id,))
    trackers = cursor.fetchall()
    
    if not trackers:
        SCAN_TASKS[user_id] = {"status": "completed", "total": 0, "completed": 0}
        conn.close()
        return

    SCAN_TASKS[user_id] = {"status": "running", "total": len(trackers), "completed": 0}
    
    cursor.execute("SELECT target_competitors FROM users WHERE id = ?", (user_id,))
    comp_row = cursor.fetchone()
    target_competitors = comp_row[0] if comp_row and comp_row[0] else None
    
    agent = HawkscanAgent()
    
    for tracker in trackers:
        t_id, product_name, company_name, platform, catalog_url = tracker
        
        # Add a small 1-second delay to prevent IP bans or rate limits
        time.sleep(1)
        
        try:
            results = agent.analyze_prices(product_name, company_name, platform, catalog_url=catalog_url, target_competitors=target_competitors)
            tokens_used = results.get('tokens_used', 0)
            
            def safe_float(v):
                try:
                    return float(v)
                except (ValueError, TypeError):
                    return None
                    
            my_price_raw = results.get("my_price")
            my_price = safe_float(my_price_raw) if my_price_raw != "Not Found" else None
            if my_price is not None:
                cursor.execute("UPDATE trackers SET baseline_price = ? WHERE id = ? AND baseline_price IS NULL", (my_price, t_id))
            
            stats = results.get("stats", {})
            market_avg = safe_float(stats.get("avg"))
            market_high = safe_float(stats.get("max"))
            market_low = safe_float(stats.get("min"))
            min_url = stats.get('min_url')
            max_url = stats.get('max_url')
            
            cursor.execute('''INSERT INTO scan_history (tracker_id, my_price, market_avg, market_high, market_low, market_high_url, market_low_url) 
                              VALUES (?, ?, ?, ?, ?, ?, ?)''', (t_id, my_price, market_avg, market_high, market_low, max_url, min_url))
            
            if market_avg is not None:
                cursor.execute('''UPDATE trackers 
                                  SET last_price = ?, last_market_avg = ?, last_market_high = ?, last_market_low = ?, 
                                      last_market_high_url = ?, last_market_low_url = ?,
                                      scan_count = scan_count + 1, updated_at = CURRENT_TIMESTAMP 
                                  WHERE id = ?''', (my_price, market_avg, market_high, market_low, max_url, min_url, t_id))
            else:
                cursor.execute('''UPDATE trackers 
                                  SET last_price = ?, scan_count = scan_count + 1, updated_at = CURRENT_TIMESTAMP 
                                  WHERE id = ?''', (my_price, t_id))
            
            if tokens_used > 0:
                cursor.execute("UPDATE users SET total_tokens_used = total_tokens_used + ? WHERE id = ?", (tokens_used, user_id))
                
            conn.commit()
        except Exception as e:
            cursor.execute("INSERT INTO error_logs (user_id, error_message, endpoint) VALUES (?, ?, ?)", (user_id, str(e), "background_scan"))
            conn.commit()
            print(f"Error scanning {product_name}: {e}")
            
        SCAN_TASKS[user_id]["completed"] += 1
        
    SCAN_TASKS[user_id]["status"] = "completed"
    conn.close()

@app.route('/api/scan/start', methods=['POST'])
@login_required_api
def api_scan_start():
    user_id = session.get('user_id')
    if user_id in SCAN_TASKS and SCAN_TASKS[user_id].get("status") == "running":
        return jsonify({"success": False, "message": "Scan already in progress"})
    
    thread = threading.Thread(target=background_scan, args=(user_id,))
    thread.daemon = True
    thread.start()
    return jsonify({"success": True})

@app.route('/api/scan/status', methods=['GET'])
@login_required_api
def api_scan_status():
    user_id = session.get('user_id')
    status = SCAN_TASKS.get(user_id, {"status": "idle", "total": 0, "completed": 0})
    return jsonify(status)

@app.route('/api/settings/competitors', methods=['GET', 'POST'])
@login_required_api
def api_settings_competitors():
    user_id = session.get('user_id')
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute("SELECT target_competitors FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        competitors = row[0] if row and row[0] else ""
        return jsonify({"competitors": competitors})
        
    elif request.method == 'POST':
        data = request.json
        competitors = data.get('competitors', '')
        cursor.execute("UPDATE users SET target_competitors = ? WHERE id = ?", (competitors, user_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "competitors": competitors})

@app.route('/api/chat', methods=['POST'])
@login_required_api
def api_chat():
    data = request.json
    message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id')
    
    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400
        
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    if not conversation_id:
        # Create new conversation
        title = message[:30] + "..." if len(message) > 30 else message
        cursor.execute("INSERT INTO conversations (user_id, title) VALUES (?, ?)", (user_id, title))
        conversation_id = cursor.lastrowid
    
    # Fetch history
    cursor.execute("SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC", (conversation_id,))
    history_rows = cursor.fetchall()
    history = [{"role": row[0], "content": row[1]} for row in history_rows]
    
    # Get reply from agent passing the history and user_id
    response_text = agent.chat(message, history, user_id=user_id)
    
    # Save new messages
    cursor.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)", (conversation_id, "user", message))
    cursor.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)", (conversation_id, "assistant", response_text))
    conn.commit()
    conn.close()
    
    action_taken = None
    if "change my price" in message.lower() or "update price" in message.lower():
        action_taken = "Price updated successfully via Hawkscan Execution Skill."
        
    return jsonify({
        "reply": response_text,
        "action": action_taken,
        "conversation_id": conversation_id
    })

@app.route('/api/conversations', methods=['GET'])
@login_required_api
def api_conversations():
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at FROM conversations WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    convs = cursor.fetchall()
    conn.close()
    return jsonify([{"id": c[0], "title": c[1], "created_at": c[2]} for c in convs])

@app.route('/api/conversations/<int:conversation_id>', methods=['GET'])
@login_required_api
def api_conversation_messages(conversation_id):
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Verify owner
    cursor.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Unauthorized"}), 403
        
    cursor.execute("SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC", (conversation_id,))
    messages = cursor.fetchall()
    conn.close()
    return jsonify([{"role": m[0], "content": m[1], "timestamp": m[2]} for m in messages])

@app.route('/api/track', methods=['POST'])
@login_required_api
def api_track():
    data = request.json
    product_name = data.get('product_name', '').strip()
    company_name = data.get('company_name', '').strip()
    platform = data.get('platform', '').strip()
    catalog_url = data.get('catalog_url', '').strip()
    
    if not all([product_name, company_name, platform]):
        return jsonify({"error": "Missing required fields"}), 400
        
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO trackers (user_id, product_name, company_name, platform, baseline_price, catalog_url) VALUES (?, ?, ?, ?, NULL, ?)",
        (user_id, product_name, company_name, platform, catalog_url)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/products/<int:product_id>', methods=['GET'])
@login_required_api
def api_product(product_id):
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, product_name, company_name, platform, baseline_price, catalog_url FROM trackers WHERE id = ? AND user_id = ?", (product_id, user_id))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({
        "id": row[0],
        "product_name": row[1],
        "company_name": row[2],
        "platform": row[3],
        "baseline_price": row[4],
        "catalog_url": row[5]
    })

@app.route('/api/trackers', methods=['GET'])
@login_required_api
def api_trackers():
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, product_name, company_name, platform, baseline_price, last_price, updated_at, is_active, catalog_url, last_market_avg, last_market_high, last_market_low, scan_count, last_market_high_url, last_market_low_url FROM trackers WHERE user_id = ?", (user_id,))
    trackers = cursor.fetchall()
    conn.close()
    return jsonify([{
        "id": t[0], "product_name": t[1], "company_name": t[2], 
        "platform": t[3], "baseline_price": t[4], "last_price": t[5], "updated_at": t[6], "is_active": bool(t[7]), "catalog_url": t[8],
        "last_market_avg": t[9], "last_market_high": t[10], "last_market_low": t[11], "scan_count": t[12],
        "last_market_high_url": t[13], "last_market_low_url": t[14]
    } for t in trackers])

@app.route('/api/history/<int:tracker_id>', methods=['GET'])
@login_required_api
def api_history_tracker(tracker_id):
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Verify owner
    cursor.execute("SELECT id FROM trackers WHERE id = ? AND user_id = ?", (tracker_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Unauthorized"}), 403
        
    cursor.execute("SELECT my_price, market_avg, market_high, market_low, timestamp FROM scan_history WHERE tracker_id = ? ORDER BY timestamp DESC", (tracker_id,))
    history_rows = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        "my_price": h[0], "market_avg": h[1], "market_high": h[2], "market_low": h[3], "timestamp": h[4]
    } for h in history_rows])

@app.route('/api/history_global', methods=['GET'])
@login_required_api
def api_history_global():
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.product_name, t.platform, s.my_price, s.market_avg, s.market_high, s.market_low, s.timestamp 
        FROM scan_history s
        JOIN trackers t ON s.tracker_id = t.id
        WHERE t.user_id = ?
        ORDER BY s.timestamp DESC
    ''', (user_id,))
    
    history_rows = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        "product_name": h[0], "platform": h[1], "my_price": h[2], 
        "market_avg": h[3], "market_high": h[4], "market_low": h[5], "timestamp": h[6]
    } for h in history_rows])

@app.route('/api/trackers/<int:product_id>/toggle', methods=['POST'])
@login_required_api
def api_toggle_tracker(product_id):
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM trackers WHERE id = ? AND user_id = ?", (product_id, user_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Tracker not found"}), 404
        
    new_status = 1 if row[0] == 0 else 0
    cursor.execute("UPDATE trackers SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, product_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "is_active": bool(new_status)})

@app.route('/api/trackers/<int:product_id>', methods=['DELETE'])
@login_required_api
def api_delete_tracker(product_id):
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trackers WHERE id = ? AND user_id = ?", (product_id, user_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if rows_affected == 0:
        return jsonify({"error": "Tracker not found"}), 404
        
    return jsonify({"success": True})

@app.route('/api/test-email', methods=['POST'])
@login_required_api
def api_test_email():
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"error": "User not found"}), 404
        
    user_email = row[0]
    
    try:
        from emailer import send_price_drop_email
        send_price_drop_email(
            to_email=user_email,
            product_name="Test Product (iPhone 15 Pro)",
            my_price=4500.00,
            competitor_price=4200.00,
            platform="Amazon.ae",
            url="https://amazon.ae",
            competitor_name="Test Competitor"
        )
        return jsonify({"success": True, "message": f"Test email sent to {user_email}!"})
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500


@app.route('/godmode')
@admin_required
def admin_dashboard():
    return render_template('admin.html')

@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def api_admin_stats():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM trackers WHERE is_active = 1")
    trackers = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(scan_count) FROM trackers")
    scans = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(total_tokens_used) FROM users")
    tokens = cursor.fetchone()[0] or 0
    conn.close()
    return jsonify({"users": users, "active_trackers": trackers, "total_scans": scans, "total_tokens": tokens})

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def api_admin_users():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''SELECT u.id, u.email, u.total_tokens_used, u.is_admin, COUNT(t.id) as trackers
                      FROM users u LEFT JOIN trackers t ON u.id = t.user_id AND t.is_active = 1
                      GROUP BY u.id''')
    users = [{"id": row[0], "email": row[1], "tokens": row[2], "is_admin": bool(row[3]), "trackers": row[4]} for row in cursor.fetchall()]
    conn.close()
    return jsonify({"users": users})

@app.route('/api/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def api_admin_delete_user(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM error_logs WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM scan_history WHERE tracker_id IN (SELECT id FROM trackers WHERE user_id = ?)", (user_id,))
    cursor.execute("DELETE FROM trackers WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id = ?)", (user_id,))
    cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM password_resets WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/admin/logs', methods=['GET'])
@admin_required
def api_admin_logs():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''SELECT e.id, u.email, e.error_message, e.endpoint, e.timestamp 
                      FROM error_logs e LEFT JOIN users u ON e.user_id = u.id 
                      ORDER BY e.timestamp DESC LIMIT 50''')
    logs = [{"id": row[0], "user": row[1] or 'System', "error": row[2], "endpoint": row[3], "timestamp": row[4]} for row in cursor.fetchall()]
    conn.close()
    return jsonify({"logs": logs})

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=run_analysis_job, trigger="interval", hours=1)
    scheduler.start()
    
    try:
        app.run(debug=True, port=5000, use_reloader=False)
    finally:
        scheduler.shutdown()