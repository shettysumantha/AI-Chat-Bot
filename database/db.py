
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
    conn.commit()
    conn.close()

def save_message(msg,res):
    conn=sqlite3.connect("chatbot.db")
    c=conn.cursor()
    c.execute("INSERT INTO conversations(user_message,bot_response) VALUES (?,?)",(msg,res))
    conn.commit()
    conn.close()
