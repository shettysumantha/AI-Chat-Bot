from flask import Flask, request, jsonify, send_from_directory, session
from models.chatbot import Chatbot
from database.db import init_db, save_message, create_user, get_user_by_email, get_user_by_id, update_user_photo

from werkzeug.security import generate_password_hash, check_password_hash
import threading
import webbrowser
import os

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')
bot = Chatbot()

init_db()


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/chat", methods=["POST"])
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
    pw_hash = generate_password_hash(password)
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
    if not check_password_hash(pw_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401
    session['user_id'] = uid
    return jsonify({'id': uid, 'name': name, 'email': uemail, 'phone': phone, 'photo': photo, 'is_admin': is_admin})


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


if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    app.run(debug=True, use_reloader=False)