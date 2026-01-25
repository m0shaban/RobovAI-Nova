import sqlite3
import json
import os
from typing import Optional, Dict, Any, List
from .security import get_password_hash, verify_password

DB_PATH = "users.db"

class Database:
    def __init__(self):
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Users Table
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    balance INTEGER DEFAULT 100
                )
            ''')
            # Logs Table
            c.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    tool_name TEXT,
                    tokens INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Conversations Table (Agent Memory)
            c.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    role TEXT, -- 'user' or 'assistant'
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            # Sessions Table (Advanced Auth)
            c.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    token TEXT UNIQUE,
                    expires_at TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            conn.commit()

    async def create_user(self, email: str, password: str, full_name: str) -> Optional[Dict[str, Any]]:
        """Create a new user"""
        try:
            password_hash = get_password_hash(password)
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)",
                    (email, password_hash, full_name)
                )
                conn.commit()
                return {"id": c.lastrowid, "email": email, "full_name": full_name}
        except sqlite3.IntegrityError:
            return None # Email already exists

    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user info"""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = c.fetchone()
            
            if user and verify_password(password, user['password_hash']):
                return dict(user)
        return None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT id, email, full_name, balance FROM users WHERE email = ?", (email,))
            user = c.fetchone()
            if user:
                return dict(user)
        return None

    # --- Existing Token Logic (Upgraded) ---

    async def get_user_balance(self, user_id: str) -> int:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE email = ? OR id = ?", (user_id, user_id))
            result = c.fetchone()
        return result[0] if result else 0

    async def deduct_tokens(self, user_id: str, amount: int) -> bool:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Check balance
            c.execute("SELECT balance FROM users WHERE email = ? OR id = ?", (user_id, user_id))
            result = c.fetchone()
            if not result or result[0] < amount:
                return False
                
            # Deduct
            c.execute("UPDATE users SET balance = balance - ? WHERE email = ? OR id = ?", (amount, user_id, user_id))
            conn.commit()
        return True

    async def log_usage(self, user_id: str, tool_name: str, tokens: int, summary: str):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO logs (user_id, tool_name, tokens) VALUES (?, ?, ?)",
                (str(user_id), tool_name, tokens)
            )
            conn.commit()

    # --- Agent Memory ---

    async def save_message(self, user_id: int, role: str, content: str):
        """Save a message to persistent memory"""
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content)
            )
            conn.commit()

    async def get_recent_messages(self, user_id: int, limit: int = 10) -> List[Dict[str, str]]:
        """Retrieve recent context for LLM"""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit)
            )
            rows = c.fetchall()
            return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    # --- Session Management (Advanced Security) ---

    async def create_session(self, user_id: int, token: str, expires_at: str):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
                (user_id, token, expires_at)
            )
            conn.commit()

    async def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM sessions WHERE token = ?", (token,))
            row = c.fetchone()
            if row:
                return dict(row)
        return None

    async def delete_session(self, token: str):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()

db_client = Database()
