import sqlite3

DB_NAME = "macromate.db"

def connect():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = connect()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        is_verified INTEGER DEFAULT 0
    )
    """)

    # Safe migration: add is_verified to any pre-existing table that lacks it.
    # SQLite raises OperationalError when the column already exists — catch only that.
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")
        print("[MacroMate] Migration: added is_verified column to users table")
    except sqlite3.OperationalError:
        pass  # Column already present — nothing to do

    # Safe migration: add role column for role-based access control.
    try:
        c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        print("[MacroMate] Migration: added role column to users table")
    except sqlite3.OperationalError:
        pass  # Column already present — nothing to do

    c.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        weight REAL,
        calories INTEGER
    )
    """)

    conn.commit()
    conn.close()