from flask import Flask, request, jsonify, send_from_directory, session
from models.chatbot import Chatbot
from database.db import init_db, save_message, create_user, get_user_by_email, get_user_by_id, update_user_photo, update_user_profile, update_user_password, print_db_backend

from werkzeug.security import generate_password_hash, check_password_hash

# bcrypt is preferred but optional for development environments
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except Exception:
    bcrypt = None
    BCRYPT_AVAILABLE = False

# JWT support is optional; only use if the installed jwt package provides encode/decode.
JWT_AVAILABLE = False
try:
    import jwt
    if hasattr(jwt, 'encode') and hasattr(jwt, 'decode'):
        JWT_AVAILABLE = True
except Exception:
    jwt = None


def hash_password(password: str) -> str:
    """Return a hashed password. Uses bcrypt when available, otherwise werkzeug."""
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    return generate_password_hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    """Verify password against stored hash supporting bcrypt and werkzeug formats."""
    if BCRYPT_AVAILABLE:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        except Exception:
            return check_password_hash(stored_hash, password)
    return check_password_hash(stored_hash, password)

import time
from datetime import datetime, timedelta
import threading
import webbrowser
import os
import smtplib
import ssl
from email.message import EmailMessage

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')
bot = Chatbot()

init_db()
print_db_backend()


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


# Serve dedicated auth pages
@app.route('/login', methods=['GET'])
def login_page():
    return send_from_directory('static', 'login.html')


@app.route('/register', methods=['GET'])
def register_page():
    return send_from_directory('static', 'register.html')


@app.route('/profile', methods=['GET'])
def profile_page():
    return send_from_directory('static', 'profile.html')


@app.route('/api/profile', methods=['GET'])
def api_profile():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'user': None}), 401
    row = get_user_by_id(uid)
    if not row:
        return jsonify({'user': None}), 404
    uid, name, email, phone, photo, is_admin = row
    return jsonify({'user': {'id': uid, 'name': name, 'email': email, 'phone': phone, 'photo': photo, 'is_admin': is_admin}})


@app.route('/api/profile', methods=['PUT'])
def api_update_profile():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    first = data.get('first_name', '').strip()
    last = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    if not (first and last and email):
        return jsonify({'error': 'Missing fields'}), 400
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Invalid email'}), 400
    name = f"{first} {last}"
    update_user_profile(uid, name, email, phone)
    return jsonify({'ok': True})


@app.route('/api/profile/upload-photo', methods=['POST'])
def api_upload_profile_photo():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Unauthorized'}), 401
    if 'photo' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    allowed = {'image/jpeg', 'image/jpg', 'image/png', 'image/webp'}
    if file.mimetype not in allowed:
        return jsonify({'error': 'Invalid file type'}), 400
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 5 * 1024 * 1024:
        return jsonify({'error': 'File too large'}), 400
    upload_dir = os.path.join(app.static_folder, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"user_{uid}_{int(time.time())}_{file.filename.replace(' ', '_')}"
    path = os.path.join(upload_dir, filename)
    file.save(path)
    url_path = f"/static/uploads/{filename}"
    update_user_photo(uid, url_path)
    return jsonify({'photo': url_path})


@app.route('/api/support', methods=['POST'])
def api_support():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()
    if not subject or not message:
        return jsonify({'error': 'Missing fields'}), 400
    support_email = os.environ.get('SUPPORT_EMAIL', 'sumanthshettytech@gmail.com')
    smtp_host = os.environ.get('SMTP_HOST')
    smtp_port = int(os.environ.get('SMTP_PORT', 0) or 0)
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    smtp_from = os.environ.get('SMTP_FROM') or smtp_user or support_email
    if smtp_host and smtp_port and smtp_user and smtp_pass:
        try:
            msg = EmailMessage()
            msg['Subject'] = f'Nexa AI Support Request: {subject}'
            msg['From'] = smtp_from
            msg['To'] = support_email
            msg.set_content(f'User ID: {uid}\nSubject: {subject}\n\n{message}')
            if smtp_port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                if os.environ.get('SMTP_TLS', '1') not in ('0', 'false', 'no'):
                    server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                server.quit()
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'ok': True})


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('user_id', None)
    return jsonify({'ok': True})


@app.route('/chat', methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "")
    response = bot.get_response(message)
    save_message(message, response)
    return jsonify({"response": response})


# Authentication routes
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    if not (name and email and password):
        return jsonify({'error': 'Missing fields'}), 400
    # Hash password (bcrypt preferred when available)
    pw_hash = hash_password(password)
    uid = create_user(name, email, phone, pw_hash)
    if not uid:
        return jsonify({'error': 'User exists or could not be created'}), 400
    session['user_id'] = uid
    return jsonify({'id': uid, 'name': name, 'email': email, 'phone': phone})


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = get_user_by_email(email)
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    # user row: id,name,email,phone,password,photo,is_admin
    uid, name, uemail, phone, pw_hash, photo, is_admin = user
    # Verify password against stored hash (supports bcrypt or werkzeug)
    if not verify_password(pw_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401
    session['user_id'] = uid
    response = {'id': uid, 'name': name, 'email': uemail, 'phone': phone, 'photo': photo, 'is_admin': is_admin}
    if JWT_AVAILABLE:
        try:
            response['token'] = jwt.encode({'sub': uid, 'exp': datetime.utcnow() + timedelta(hours=4)}, app.secret_key, algorithm='HS256')
        except Exception:
            response['token'] = None
    return jsonify(response)


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'ok': True})


@app.route('/me')
def me():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'user': None})
    row = get_user_by_id(uid)
    if not row:
        return jsonify({'user': None})
    # row: id,name,email,phone,photo,is_admin
    uid, name, email, phone, photo, is_admin = row
    return jsonify({'user': {'id': uid, 'name': name, 'email': email, 'phone': phone, 'photo': photo, 'is_admin': is_admin}})


@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Unauthorized'}), 401
    if 'photo' not in request.files:
        return jsonify({'error': 'No file'}), 400
    f = request.files['photo']
    upload_dir = os.path.join(app.static_folder, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"user_{uid}_" + f.filename.replace(' ', '_')
    path = os.path.join(upload_dir, filename)
    f.save(path)
    url_path = f"/static/uploads/{filename}"
    update_user_photo(uid, url_path)
    return jsonify({'photo': url_path})


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")


# --- OTP and auth helper endpoints (minimal implementations) ---

_otp_store = {}

def _cleanup_otps():
    now = time.time()
    keys = [k for k, v in _otp_store.items() if v.get('expires_at', 0) < now]
    for k in keys:
        _otp_store.pop(k, None)


@app.route('/api/send-otp', methods=['POST'])
def api_send_otp():
    data = request.json or {}
    contact = data.get('contact')
    method = data.get('method', 'email')
    if not contact:
        return jsonify({'error': 'Missing contact'}), 400
    _cleanup_otps()
    key = f"{method}:{contact}"
    now = time.time()
    entry = _otp_store.get(key)
    if entry and now - entry.get('last_sent', 0) < 15:
        return jsonify({'error': 'Rate limited'}), 429
    # For development/testing default OTP can be fixed. Use DEV_OTP env var to override.
    otp = os.environ.get('DEV_OTP', '123456')
    _otp_store[key] = {'otp': otp, 'attempts': 0, 'last_sent': now, 'expires_at': now + 300}
    sent = False
    send_error = None
    # Try to send via SMTP when method=email and SMTP vars present
    if method == 'email':
        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = int(os.environ.get('SMTP_PORT', 0) or 0)
        smtp_user = os.environ.get('SMTP_USER')
        smtp_pass = os.environ.get('SMTP_PASS')
        smtp_from = os.environ.get('SMTP_FROM') or smtp_user
        use_tls = os.environ.get('SMTP_TLS', '1') not in ('0', 'false', 'no')
        if smtp_host and smtp_port and smtp_user and smtp_pass:
            try:
                msg = EmailMessage()
                msg['Subject'] = 'Your Nexa AI verification code'
                msg['From'] = smtp_from
                msg['To'] = contact
                msg.set_content(f'Your Nexa verification code is: {otp}\nThis code expires in 5 minutes.')
                if smtp_port == 465:
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                        server.login(smtp_user, smtp_pass)
                        server.send_message(msg)
                else:
                    server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                    if use_tls:
                        server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                    server.quit()
                sent = True
            except Exception as e:
                send_error = str(e)

    # TODO: add Twilio or other SMS provider when configured (not implemented here)

    # Return success info; include debug_otp only in development or when not sent
    resp = {'ok': True, 'method': method, 'masked': contact, 'sent': sent}
    if send_error:
        resp['error'] = send_error
    # Include debug OTP for local dev convenience
    if os.environ.get('DEV_SHOW_OTP', '1') == '1' or not sent:
        resp['debug_otp'] = otp
    return jsonify(resp)


@app.route('/api/verify-otp', methods=['POST'])
def api_verify_otp():
    data = request.json or {}
    contact = data.get('contact')
    method = data.get('method', 'email')
    code = data.get('code')
    if not (contact and code):
        return jsonify({'error': 'Missing data'}), 400
    key = f"{method}:{contact}"
    entry = _otp_store.get(key)
    if not entry:
        return jsonify({'error': 'OTP expired or not found'}), 400
    if entry['attempts'] >= 3:
        return jsonify({'error': 'Maximum attempts exceeded'}), 400
    if time.time() > entry['expires_at']:
        return jsonify({'error': 'OTP expired'}), 400
    entry['attempts'] += 1
    if entry['otp'] != code:
        return jsonify({'error': 'Invalid OTP'}), 400
    # success
    _otp_store.pop(key, None)
    return jsonify({'ok': True})


@app.route('/api/resend-otp', methods=['POST'])
def api_resend_otp():
    data = request.json or {}
    contact = data.get('contact')
    method = data.get('method', 'email')
    if not contact:
        return jsonify({'error': 'Missing contact'}), 400
    key = f"{method}:{contact}"
    # allow resend by calling send-otp again
    return api_send_otp()


@app.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.json or {}
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Missing email'}), 400
    user = get_user_by_email(email)
    if not user:
        return jsonify({'ok': True})
    # send OTP to email
    return api_send_otp()


@app.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    data = request.json or {}
    email = data.get('email')
    code = data.get('code')
    new_password = data.get('new_password')
    if not (email and code and new_password):
        return jsonify({'error': 'Missing fields'}), 400
    # verify otp
    v = api_verify_otp()
    if v.status_code != 200:
        return v
    # update password
    # hash new password
    pw_hash = hash_password(new_password)
    update_user_password(email, pw_hash)
    return jsonify({'ok': True})


if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    app.run(debug=True, use_reloader=False)