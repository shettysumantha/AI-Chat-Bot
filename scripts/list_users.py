import sqlite3

def list_users():
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    try:
        c.execute('SELECT id,name,email,phone,photo,is_admin FROM users')
        rows = c.fetchall()
        for r in rows:
            print(r)
    except Exception as e:
        print('Error querying users:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    list_users()
