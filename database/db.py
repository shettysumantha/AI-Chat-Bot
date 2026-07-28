"""PostgreSQL database helpers.

This module uses PostgreSQL exclusively. It expects either a DATABASE_URL or the
PG_* environment variables to be available and raises a clear error if no
compatible driver is installed.
"""

import os
import urllib.parse
from pathlib import Path

DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("PG_DATABASE_URL")
PG_AVAILABLE = False
DB_DRIVER = None
psycopg2 = None
pg8000 = None

DB_CONFIG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", 5432)),
    "database": os.environ.get("PG_DATABASE", "MyDatabase"),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD", "Shetty123@"),
}

print("DATABASE_URL =", DATABASE_URL)
print("PG_HOST =", DB_CONFIG["host"])
print("PG_DATABASE =", DB_CONFIG["database"])

try:
    import psycopg2
    PG_AVAILABLE = True
    DB_DRIVER = "psycopg2"
except Exception as exc:
    try:
        import pg8000
        PG_AVAILABLE = True
        DB_DRIVER = "pg8000"
        print("INFO: psycopg2 failed, using pg8000 as PostgreSQL driver.")
    except Exception as exc2:
        raise RuntimeError("PostgreSQL driver is not available. Install psycopg2 or pg8000.") from exc2


def get_db_backend():
    return f"PostgreSQL ({DB_DRIVER})"


def _mask_secret(value):
    if value is None:
        return "None"
    if value == "":
        return "EMPTY"
    return value[:1] + "***" + value[-1:]


def _build_pg_config():
    if DATABASE_URL:
        parsed = urllib.parse.urlparse(DATABASE_URL)
        db_name = parsed.path.lstrip("/")
        user = parsed.username
        password = parsed.password
        print(
            f"INFO: Parsed DATABASE_URL: user={_mask_secret(user)}, host={parsed.hostname}, port={parsed.port or 5432}, database={db_name}"
        )
        if DB_DRIVER == "psycopg2":
            return DATABASE_URL
        return {
            "user": user or DB_CONFIG["user"],
            "password": password or DB_CONFIG["password"],
            "host": parsed.hostname or DB_CONFIG["host"],
            "port": parsed.port or DB_CONFIG["port"],
            "database": db_name or DB_CONFIG["database"],
        }
    return DB_CONFIG


def get_connection():
    if DB_DRIVER == "psycopg2":
        config = _build_pg_config()
        print(f"INFO: Connecting to PostgreSQL via psycopg2 using {DB_CONFIG['host']}/{DB_CONFIG['database']}")
        if isinstance(config, str):
            return psycopg2.connect(config)
        return psycopg2.connect(**config)

    config = _build_pg_config()
    print(f"INFO: Connecting to PostgreSQL via pg8000 using {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    return pg8000.connect(**config)


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations(
            id BIGSERIAL PRIMARY KEY,
            user_message TEXT,
            bot_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
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
        """
    )
    cur.execute(Path(__file__).with_name('tables.sql').read_text(encoding='utf-8'))
    cur.execute("ALTER TABLE kb_conversations ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'waiting_for_documents'")
    cur.execute("ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS checksum TEXT")
    conn.commit()
    cur.close()
    conn.close()

    function_sql = Path(__file__).with_name('functions.sql').read_text(encoding='utf-8')
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DROP FUNCTION IF EXISTS fn_get_user_conversations(bigint)")
    cur.execute("DROP FUNCTION IF EXISTS fn_update_conversation_status(bigint, bigint, text)")
    cur.execute(function_sql)
    conn.commit()
    cur.close()
    conn.close()


def print_db_backend():
    backend = get_db_backend()
    print(f"Using database backend: {backend}")
    try:
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SHOW server_version")
            version = cur.fetchone()[0]
            print(f"PostgreSQL connected, server_version={version}")
        finally:
            cur.close()
            conn.close()
    except Exception as exc:
        print("ERROR: Could not verify PostgreSQL connection details.", exc)


def save_message(msg, res):
    conn = get_connection()
    cur = conn.cursor()
    try:
        print(f"DEBUG: Inserting conversation row to PostgreSQL: message={msg!r}")
        cur.execute("INSERT INTO conversations(user_message, bot_response) VALUES (%s, %s)", (msg, res))
        conn.commit()
        print(f"DEBUG: Conversation row inserted, rowcount={cur.rowcount}")
    except Exception as exc:
        print("ERROR: Failed to insert conversation row into PostgreSQL.", exc)
        raise
    finally:
        cur.close()
        conn.close()


def create_user(name, email, phone, password_hash, is_admin=0):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users(name, email, phone, password, is_admin) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (name, email, phone, password_hash, bool(is_admin)),
        )
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


def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id,name,email,phone,password,photo,is_admin FROM users WHERE email=%s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_user_by_id(uid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id,name,email,phone,photo,is_admin FROM users WHERE id=%s", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def update_user_photo(uid, photo_path):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET photo=%s WHERE id=%s", (photo_path, uid))
    conn.commit()
    cur.close()
    conn.close()


def update_user_profile(uid, name, email, phone):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET name=%s, email=%s, phone=%s WHERE id=%s", (name, email, phone, uid))
    conn.commit()
    cur.close()
    conn.close()


def update_user_password(email, password_hash):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password=%s WHERE email=%s", (password_hash, email))
    conn.commit()
    cur.close()
    conn.close()