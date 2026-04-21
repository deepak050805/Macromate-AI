import os
import psycopg2


def connect():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))


def init_db():
    conn = connect()
    c = conn.cursor()

    # USERS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT,
        is_verified INTEGER DEFAULT 0,
        role TEXT DEFAULT 'user'
    )
    """)

    # PROGRESS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        id SERIAL PRIMARY KEY,
        email TEXT,
        weight REAL,
        calories INTEGER
    )
    """)

    conn.commit()
    conn.close()