# database/db.py
import sqlite3
import os

DB_FILENAME = "bankbot.db"
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", DB_FILENAME))

MIGRATION_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_no TEXT UNIQUE NOT NULL,
  username TEXT NOT NULL,
  display_name TEXT NOT NULL,
  type TEXT NOT NULL,
  balance INTEGER NOT NULL DEFAULT 0,
  pin TEXT,
  card_number TEXT,
  card_status TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_no TEXT NOT NULL,
  card_number TEXT NOT NULL,
  expiry TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (account_no) REFERENCES accounts(account_no) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  from_acc TEXT,
  to_acc TEXT,
  amount INTEGER NOT NULL,
  date TEXT NOT NULL,
  type TEXT NOT NULL,
  description TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (from_acc) REFERENCES accounts(account_no),
  FOREIGN KEY (to_acc) REFERENCES accounts(account_no)
);
"""

def get_db_path() -> str:
    """Return absolute path to the DB file."""
    return DB_PATH

def get_conn():
    """Return a sqlite3 connection to the DB (creates file if missing)."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db() -> str:
    """Create tables if they do not exist and return DB path."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(MIGRATION_SQL)
    conn.commit()
    conn.close()
    return DB_PATH
