
import sqlite3

def init_db():
    conn=sqlite3.connect("chatbot.db")
    c=conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS conversations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_message TEXT,
    bot_response TEXT
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
    is_admin INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

def save_message(msg,res):
    conn=sqlite3.connect("chatbot.db")
    c=conn.cursor()
    c.execute("INSERT INTO conversations(user_message,bot_response) VALUES (?,?)",(msg,res))
    conn.commit()
    conn.close()

def create_user(name,email,phone,password_hash,is_admin=0):
    conn=sqlite3.connect("chatbot.db")
    c=conn.cursor()
    try:
        c.execute("INSERT INTO users(name,email,phone,password,is_admin) VALUES (?,?,?,?,?)",(name,email,phone,password_hash,is_admin))
        conn.commit()
        return c.lastrowid
    except Exception:
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    conn=sqlite3.connect("chatbot.db")
    c=conn.cursor()
    c.execute("SELECT id,name,email,phone,password,photo,is_admin FROM users WHERE email=?",(email,))
    row=c.fetchone()
    conn.close()
    return row

def get_user_by_id(uid):
    conn=sqlite3.connect("chatbot.db")
    c=conn.cursor()
    c.execute("SELECT id,name,email,phone,photo,is_admin FROM users WHERE id=?",(uid,))
    row=c.fetchone()
    conn.close()
    return row

def update_user_photo(uid,photo_path):
    conn=sqlite3.connect("chatbot.db")
    c=conn.cursor()
    c.execute("UPDATE users SET photo=? WHERE id=?",(photo_path,uid))
    conn.commit()
    conn.close()
