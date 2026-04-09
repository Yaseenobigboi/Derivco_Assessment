# this must set up the database and create tables on first run

import sqlite3

DATABASE = 'mzansibuilds.db'


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            stage TEXT,
            support_required TEXT,
            progress INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()
