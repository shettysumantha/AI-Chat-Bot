"""Database helpers with SQLite fallback.

This file prefers PostgreSQL when `USE_POSTGRES` is set and psycopg2 is
available. On development machines (Windows) where psycopg2 may not be
installed, it falls back to a local SQLite database `chatbot.db`.
"""

import os
import sqlite3

DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('PG_DATABASE_URL')
USE_POSTGRES = DATABASE_URL or os.environ.get('USE_POSTGRES', '').lower() in ('1', 'true', 'yes')
PG_AVAILABLE = False
psycopg2 = None
if USE_POSTGRES:
    try:
        import psycopg2
        PG_AVAILABLE = True
    except Exception as exc:
        PG_AVAILABLE = False
        print('WARNING: PostgreSQL requested but psycopg2 is not installed. Falling back to SQLite.', exc)

# Postgres config (only used when psycopg2 is available and DATABASE_URL is unavailable)
DB_CONFIG = {
    'host': os.environ.get('PG_HOST', 'localhost'),
      $env:DATABASE_URL="postgresql://postgres:YourPassword@localhost:5432/YourDatabase"
    python app.py  'port': int(os.environ.get('PG_PORT', 5432)),
    'database': os.environ.get('PG_DATABASE', 'MyDatabase'),
    'user': os.environ.get('PG_USER', 'postgres'),
    'password': os.environ.get('PG_PASSWORD', 'Shetty123@'),
}

SQLITE_PATH = os.environ.get('SQLITE_PATH', 'chatbot.db')


def get_db_backend():
    if PG_AVAILABLE:
        return 'PostgreSQL'
    return 'SQLite'


def get_connection():
    if PG_AVAILABLE:
        if DATABASE_URL:
            return psycopg2.connect(DATABASE_URL)
        return psycopg2.connect(**DB_CONFIG)
    return sqlite3.connect(SQLITE_PATH)


def init_db():
    if PG_AVAILABLE:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS conversations(
            id BIGSERIAL PRIMARY KEY,
            user_message TEXT,
            bot_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(255) UNIQUE,
            phone VARCHAR(20),
            password TEXT,
            photo TEXT,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS conversations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            bot_response TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            password TEXT,
            photo TEXT,
            is_admin INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        conn.close()


def print_db_backend():
    print(f"Using database backend: {get_db_backend()}")


def save_message(msg, res):
    if PG_AVAILABLE:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO conversations(user_message, bot_response) VALUES (%s, %s)", (msg, res))
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO conversations(user_message, bot_response) VALUES (?, ?)", (msg, res))
        conn.commit()
        conn.close()


def create_user(name, email, phone, password_hash, is_admin=0):
    if PG_AVAILABLE:
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users(name, email, phone, password, is_admin) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                        (name, email, phone, password_hash, is_admin))
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id
        except Exception as e:
            conn.rollback()
            print(e)
            return None
        finally:
            cur.close()
            conn.close()
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users(name, email, phone, password, is_admin) VALUES (?, ?, ?, ?, ?)",
                      (name, email, phone, password_hash, int(is_admin)))
            conn.commit()
            return c.lastrowid
        except Exception as e:
            conn.rollback()
            # simple logging for dev
            print(e)
            return None
        finally:
            conn.close()


def get_user_by_email(email):
    if PG_AVAILABLE:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id,name,email,phone,password,photo,is_admin FROM users WHERE email=%s", (email,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        c = conn.cursor()
        c.execute("SELECT id,name,email,phone,password,photo,is_admin FROM users WHERE email=?", (email,))
        row = c.fetchone()
        conn.close()
        return row


def get_user_by_id(uid):
    if PG_AVAILABLE:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id,name,email,phone,photo,is_admin FROM users WHERE id=%s", (uid,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        c = conn.cursor()
        c.execute("SELECT id,name,email,phone,photo,is_admin FROM users WHERE id=?", (uid,))
        row = c.fetchone()
        conn.close()
        return row


def update_user_photo(uid, photo_path):
    if PG_AVAILABLE:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET photo=%s WHERE id=%s", (photo_path, uid))
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET photo=? WHERE id=?", (photo_path, uid))
        conn.commit()
        conn.close()


def update_user_profile(uid, name, email, phone):
    if PG_AVAILABLE:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET name=%s, email=%s, phone=%s WHERE id=%s", (name, email, phone, uid))
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET name=?, email=?, phone=? WHERE id=?", (name, email, phone, uid))
        conn.commit()
        conn.close()


def update_user_password(email, password_hash):
    if PG_AVAILABLE:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password=%s WHERE email=%s", (password_hash, email))
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET password=? WHERE email=?", (password_hash, email))
        conn.commit()
        conn.close()