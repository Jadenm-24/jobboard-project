import sqlite3
from datetime import datetime,timezone

conn = sqlite3.connect("items.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()


def delete_expired_refresh_tokens():
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "DELETE FROM refresh_tokens WHERE expires_at < ?",
        (now,)
    )
    conn.commit()


def create_tables():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user'
    )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        applicant_name TEXT NOT NULL,
        applicant_email TEXT NOT NULL,
        applied_at TEXT NOT NULL,
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    )
    """)

    conn.commit()
