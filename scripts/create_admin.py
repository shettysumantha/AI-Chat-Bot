import os
import sqlite3
from werkzeug.security import generate_password_hash

# Self-contained admin creation script
# Edit these values if needed
NAME = "Admin User"
EMAIL = "admin@example.com"
PHONE = "1234567890"
PASSWORD = "ChangeMe123"

def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(base, 'chatbot.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        password TEXT,
        photo TEXT,
        is_admin INTEGER DEFAULT 0
    )''')
    pw_hash = generate_password_hash(PASSWORD)
    try:
        c.execute('INSERT OR IGNORE INTO users(name,email,phone,password,is_admin) VALUES(?,?,?,?,1)',(NAME,EMAIL,PHONE,pw_hash))
        conn.commit()
        c.execute('SELECT id FROM users WHERE email=?',(EMAIL,))
        row=c.fetchone()
        if row:
            msg = f'Created admin user id: {row[0]}'
        else:
            msg = 'Admin user not created (may already exist)'
    except Exception as e:
        msg = f'Error creating admin: {e}'
    finally:
        conn.close()
    print(msg)
    try:
        with open(os.path.join(os.path.dirname(__file__),'create_admin.log'),'a',encoding='utf-8') as f:
            f.write(msg + '\n')
    except Exception:
        pass

if __name__ == '__main__':
    main()
