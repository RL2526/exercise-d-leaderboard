import sqlite3

conn = sqlite3.connect("data.db")
conn.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    current_score REAL NOT NULL DEFAULT 0.0,
    max_score REAL NOT NULL DEFAULT 0.0,
    last_updated INTEGER NOT NULL DEFAULT 0
);
""")
conn.commit()
conn.close()