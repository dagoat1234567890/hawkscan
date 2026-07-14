import os
import sqlite3

def install_otp():
    # 1. Database Update
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            expires_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

    # 2. Emailer Update
    otp_func = """
def send_otp_email(to_email, code):
    import os, smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    smtp_email = os.environ.get("SMTP_EMAIL")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    if not smtp_email or not smtp_password:
        print("SMTP_EMAIL or SMTP_PASSWORD not configured. Cannot send OTP email.")
        return False

    subject = "Your Hawkscan Security Code"
    html_content = f\"\"\"
    <html>
    <head>
        <style>
            body {{ font-family: 'Inter', Helvetica, Arial, sans-serif; background-color: #f4f4f5; margin: 0; padding: 20px; color: #1f2937; }}
            .container {{ max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); padding: 30px; text-align: center; }}
            h2 {{ color: #1f2937; margin-bottom: 20px; }}
            p {{ font-size: 16px; line-height: 1.5; color: #4b5563; }}
            .code-box {{ background: #f3f4f6; border-radius: 8px; padding: 20px; font-size: 32px; font-weight: 700; letter-spacing: 0.2em; color: #4f46e5; margin: 20px 0; }}
            .footer {{ margin-top: 30px; color: #9ca3af; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Hawkscan Login Verification</h2>
            <p>Please enter the following 6-digit code to access your account. This code expires in 10 minutes.</p>
            <div class="code-box">{code}</div>
            <div class="footer">If you didn't attempt to log in, please reset your password immediately.</div>
        </div>
    </body>
    </html>
    \"\"\"
    
    msg = MIMEMultipart('alternative')
    msg['From'] = f"Hawkscan Security <{smtp_email}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(f"Your verification code is: {code}", 'plain'))
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        return False
"""
    with open('emailer.py', 'r', encoding='utf-8') as f:
        emailer_content = f.read()
    if "def send_otp_email" not in emailer_content:
        with open('emailer.py', 'a', encoding='utf-8') as f:
            f.write(otp_func)

    # 3. App logic
    with open('app.py', 'r', encoding='utf-8', newline='') as f:
        app_content = f.read().replace('\r\n', '\n')

    old_login = """        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['is_admin'] = bool(user[2])
            return redirect(url_for('dashboard'))"""
            
    new_login = """        if user and check_password_hash(user[1], password):
            import secrets
            from datetime import datetime, timedelta
            from emailer import send_otp_email
            
            code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            expires = (datetime.utcnow() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
            
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("INSERT INTO otps (user_id, code, expires_at) VALUES (?, ?, ?)", (user[0], code, expires))
            conn.commit()
            conn.close()
            
            session['pending_user_id'] = user[0]
            session['pending_is_admin'] = bool(user[2])
            
            success = send_otp_email(email, code)
            if not success:
                flash(f"DEV MODE: Your OTP code is {code}")
            
            return redirect(url_for('verify_otp'))"""

    app_content = app_content.replace(old_login, new_login)

    old_signup = """            session['user_id'] = new_user[0]
            return redirect(url_for('dashboard'))"""

    new_signup = """            import secrets
            from datetime import datetime, timedelta
            from emailer import send_otp_email
            
            code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            expires = (datetime.utcnow() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
            
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("INSERT INTO otps (user_id, code, expires_at) VALUES (?, ?, ?)", (new_user[0], code, expires))
            conn.commit()
            conn.close()
            
            session['pending_user_id'] = new_user[0]
            session['pending_is_admin'] = False
            
            success = send_otp_email(email, code)
            if not success:
                flash(f"DEV MODE: Your OTP code is {code}")
                
            return redirect(url_for('verify_otp'))"""

    app_content = app_content.replace(old_signup, new_signup)

    verify_route = """
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'pending_user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        user_id = session['pending_user_id']
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Clean expired
        cursor.execute("DELETE FROM otps WHERE expires_at < datetime('now')")
        conn.commit()
        
        cursor.execute("SELECT id FROM otps WHERE user_id = ? AND code = ?", (user_id, code))
        otp_record = cursor.fetchone()
        
        if otp_record:
            cursor.execute("DELETE FROM otps WHERE id = ?", (otp_record[0],))
            conn.commit()
            conn.close()
            
            session['user_id'] = session.pop('pending_user_id')
            session['is_admin'] = session.pop('pending_is_admin', False)
            
            return redirect(url_for('dashboard'))
        else:
            conn.close()
            flash("Invalid or expired code.")
            return render_template('verify_otp.html')
            
    return render_template('verify_otp.html')
"""
    if "@app.route('/verify-otp'" not in app_content:
        app_content += verify_route

    with open('app.py', 'w', encoding='utf-8', newline='\n') as f:
        f.write(app_content)

    # 4. Create Template
    template_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Access - Hawkscan</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f3f4f6; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        .auth-container { background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); width: 100%; max-width: 400px; text-align: center; }
        .auth-header h1 { font-size: 24px; font-weight: 700; color: #111827; margin-bottom: 8px; }
        .auth-header p { color: #6b7280; font-size: 14px; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; text-align: left; }
        .form-group label { display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px; }
        .form-control { width: 100%; padding: 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 20px; text-align: center; letter-spacing: 4px; font-family: monospace; box-sizing: border-box; }
        .form-control:focus { outline: none; border-color: #4f46e5; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1); }
        .btn-primary { width: 100%; padding: 12px; background: #4f46e5; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: background 0.2s; margin-top: 10px; }
        .btn-primary:hover { background: #4338ca; }
        .flash-messages { margin-bottom: 20px; text-align: left; }
        .flash-message { padding: 12px; border-radius: 8px; font-size: 14px; background-color: #fee2e2; color: #991b1b; border: 1px solid #f87171; margin-bottom: 10px; }
        .back-link { display: inline-block; margin-top: 20px; color: #4f46e5; text-decoration: none; font-size: 14px; }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="auth-container">
        <div class="auth-header">
            <h1>Security Verification</h1>
            <p>We've sent a 6-digit code to your email.</p>
        </div>

        <div class="flash-messages">
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="flash-message">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>

        <form method="POST" action="{{ url_for('verify_otp') }}">
            <div class="form-group">
                <label for="code">Enter 6-Digit Code</label>
                <input type="text" id="code" name="code" class="form-control" placeholder="000000" maxlength="6" pattern="\\d{6}" autocomplete="one-time-code" required autofocus>
            </div>
            
            <button type="submit" class="btn-primary">Verify Access</button>
        </form>
        
        <a href="{{ url_for('login') }}" class="back-link">Return to Login</a>
    </div>
</body>
</html>"""
    os.makedirs('templates', exist_ok=True)
    with open('templates/verify_otp.html', 'w', encoding='utf-8') as f:
        f.write(template_html)

if __name__ == "__main__":
    install_otp()
