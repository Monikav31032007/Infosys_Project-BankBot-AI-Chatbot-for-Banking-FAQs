# database/bank_crud.py

import sqlite3
import datetime
import pandas as pd
from typing import List, Tuple, Optional
from . import db, security

DB_PATH = db.get_db_path()

def get_conn():
    return sqlite3.connect(DB_PATH)

# Users
def create_user(username: str, password: str):
    conn = get_conn()
    cur = conn.cursor()
    pwd_hash = security.hash_password(password)
    cur.execute("INSERT OR IGNORE INTO users(username, password_hash, active) VALUES (?, ?, 1)", (username, pwd_hash))
    conn.commit()
    conn.close()

def verify_user_login(username: str, password: str) -> bool:
    if not username or not password:
        return False
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT password_hash, active FROM users WHERE username=?", (username.strip(),))
    row = cur.fetchone()
    conn.close()
    return bool(row and int(row[1]) == 1 and security.verify_password(password.strip(), row[0]))

def list_users() -> List[Tuple[str]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users")
    rows = cur.fetchall()
    conn.close()
    return rows

# Accounts
def create_account(user_name: str, acc_no: str, acc_name: str, acc_type: str, balance: int, pin: str):
    conn = get_conn()
    cur = conn.cursor()
    # ensure user exists
    cur.execute("SELECT username FROM users WHERE username=?", (user_name,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(username, password_hash, active) VALUES (?, ?, 1)", (user_name, security.hash_password("0000")))
    cur.execute("""
    INSERT OR IGNORE INTO accounts(account_no, username, display_name, type, balance, pin)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (acc_no, user_name, acc_name, acc_type, balance, pin))
    conn.commit()
    conn.close()

def list_user_accounts(user_name: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT account_no, display_name, type, balance FROM accounts WHERE username=?", (user_name,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_account(acc_no: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT account_no, username, type, balance, pin FROM accounts WHERE account_no=?", (acc_no,))
    row = cur.fetchone()
    conn.close()
    return row

def verify_account_password(acc_no: str, pin: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT pin FROM accounts WHERE account_no=?", (acc_no,))
    row = cur.fetchone()
    conn.close()
    return bool(row and str(row[0]) == str(pin))

# Transfers
def transfer_money(from_acc: str, to_acc: str, amount: int, pin: str) -> str:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT balance, pin FROM accounts WHERE account_no=?", (from_acc,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return "❌ Invalid sender account"
    balance, stored_pin = row
    if str(stored_pin) != str(pin):
        conn.close()
        return "❌ Incorrect PIN"
    if balance < amount:
        conn.close()
        return "❌ Insufficient balance"
    cur.execute("SELECT balance FROM accounts WHERE account_no=?", (to_acc,))
    row2 = cur.fetchone()
    if not row2:
        conn.close()
        return "❌ Recipient account not found"
    try:
        cur.execute("BEGIN")
        cur.execute("UPDATE accounts SET balance = balance - ? WHERE account_no=?", (amount, from_acc))
        cur.execute("UPDATE accounts SET balance = balance + ? WHERE account_no=?", (amount, to_acc))
        now = datetime.datetime.utcnow().isoformat()
        cur.execute("INSERT INTO transactions(from_acc, to_acc, amount, date, type, description) VALUES (?,?,?,?,?,?)",
                    (from_acc, to_acc, amount, now, "debit", f"Transfer to {to_acc}"))
        cur.execute("INSERT INTO transactions(from_acc, to_acc, amount, date, type, description) VALUES (?,?,?,?,?,?)",
                    (from_acc, to_acc, amount, now, "credit", f"Received from {from_acc}"))
        conn.commit()
        return f"✅ Transferred ₹{amount} from {from_acc} to {to_acc}."
    except Exception as e:
        conn.rollback()
        return f"❌ Transfer failed: {e}"
    finally:
        conn.close()

# Cards
def add_card(account_no: str, card_number: str, expiry: str = "12/30"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO cards(account_no, card_number, expiry) VALUES (?, ?, ?)", (account_no, card_number, expiry))
    conn.commit()
    conn.close()

def block_card_for_account(account_no: str) -> str:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM cards WHERE account_no=?", (account_no,))
        deleted = cur.rowcount
        conn.commit()
        if deleted > 0:
            return f"✅ Card linked to account {account_no} blocked and removed."
        else:
            return f"⚠️ No card found for account {account_no}."
    except Exception as e:
        conn.rollback()
        return f"❌ Error blocking card: {e}"
    finally:
        conn.close()

# Transactions / History
def list_transactions_for_user(user_name: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT t.id, t.from_acc, t.to_acc, t.amount, t.date, t.type
    FROM transactions t
    JOIN accounts a ON a.account_no = t.from_acc OR a.account_no = t.to_acc
    WHERE a.username=?
    ORDER BY t.date DESC
    """, (user_name,))
    rows = cur.fetchall()
    conn.close()
    return rows

def transactions_to_dataframe(txns: List[Tuple]) -> pd.DataFrame:
    if not txns:
        return pd.DataFrame(columns=["id","from","to","amount","date","type"])
    df = pd.DataFrame(txns, columns=["id","from","to","amount","date","type"])
    try:
        df["date"] = pd.to_datetime(df["date"])
    except:
        pass
    try:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0).astype(int)
    except:
        pass
    return df
