"""
🗄️ RobovAI Nova — Database Layer
═══════════════════════════════════════════
• User roles (user / admin)
• Atomic balance deduction (no race conditions)
• Indexes for performance
• Subscription tiers
• Usage tracking per day
"""

import sqlite3
import json
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from .security import get_password_hash, verify_password_and_update

DB_PATH = os.getenv("DATABASE_PATH", "users.db")
logger = logging.getLogger("robovai.database")


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


class Database:
    def __init__(self):
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        """Initialize SQLite database with roles, indexes, and proper schema."""
        with self._get_conn() as conn:
            c = conn.cursor()

            # Users Table — with role field
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    balance INTEGER DEFAULT 100,
                    daily_used INTEGER DEFAULT 0,
                    daily_reset_date TEXT,
                    subscription_tier TEXT DEFAULT 'free',
                    subscription_expires TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Add missing columns to existing tables (safe migration)
            for col, defn in [
                ("role", "TEXT DEFAULT 'user'"),
                ("daily_used", "INTEGER DEFAULT 0"),
                ("daily_reset_date", "TEXT"),
                ("subscription_tier", "TEXT DEFAULT 'free'"),
                ("subscription_expires", "TEXT"),
                ("updated_at", "TIMESTAMP"),
                ("is_verified", "INTEGER DEFAULT 0"),
                ("telegram_chat_id", "TEXT"),
            ]:
                try:
                    c.execute(f"ALTER TABLE users ADD COLUMN {col} {defn}")
                except sqlite3.OperationalError:
                    pass  # Column already exists

            # Sessions Table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    token TEXT UNIQUE,
                    expires_at TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """
            )

            # Logs Table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    tool_name TEXT,
                    tokens INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Conversations Table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    role TEXT,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """
            )

            # Subscriptions Table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE,
                    tier TEXT DEFAULT 'free',
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # OTP Codes Table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS otp_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    code TEXT,
                    purpose TEXT,
                    expires_at TIMESTAMP,
                    used INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Usage Logs Table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    tool_name TEXT,
                    tokens_cost INTEGER DEFAULT 0,
                    platform TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Add tokens_cost column if missing
            try:
                c.execute(
                    "ALTER TABLE usage_logs ADD COLUMN tokens_cost INTEGER DEFAULT 0"
                )
            except sqlite3.OperationalError:
                pass

            # ── Indexes ──
            for idx in [
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_usage_logs_user_date ON usage_logs(user_id, timestamp)",
            ]:
                c.execute(idx)

            # ── Custom Bots Table ──
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS custom_bots (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    system_prompt TEXT NOT NULL,
                    avatar_emoji TEXT DEFAULT '🤖',
                    tools TEXT DEFAULT '[]',
                    greeting TEXT DEFAULT 'مرحباً!',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.commit()
            logger.info("✅ Database initialized with roles, indexes, and billing")

    # ═══════════════════════════════════════════════════════════════
    # 👤 USER MANAGEMENT
    # ═══════════════════════════════════════════════════════════════

    async def create_user(
        self, email: str, password: str, full_name: str, role: str = "user"
    ) -> Optional[Dict[str, Any]]:
        try:
            email = _normalize_email(email)
            password_hash = get_password_hash(password)
            today = datetime.now().strftime("%Y-%m-%d")
            with self._get_conn() as conn:
                c = conn.cursor()
                c.execute(
                    """INSERT INTO users (email, password_hash, full_name, role, balance, daily_used, daily_reset_date)
                       VALUES (?, ?, ?, ?, 100, 0, ?)""",
                    (email, password_hash, full_name, role, today),
                )
                conn.commit()
                return {
                    "id": c.lastrowid,
                    "email": email,
                    "full_name": full_name,
                    "role": role,
                    "balance": 100,
                }
        except sqlite3.IntegrityError:
            return None
        except Exception as e:
            logger.exception(f"create_user error: {e}")
            raise

    async def authenticate_user(
        self, email: str, password: str
    ) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            # Case-insensitive email match to avoid login failures due to casing.
            c.execute(
                "SELECT * FROM users WHERE lower(email) = lower(?)",
                (_normalize_email(email),),
            )
            user = c.fetchone()
            if not user:
                return None

            ok, new_hash = verify_password_and_update(password, user["password_hash"])
            if not ok:
                return None

            # Opportunistically upgrade legacy hashes.
            if new_hash:
                try:
                    c.execute(
                        "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (new_hash, user["id"]),
                    )
                    conn.commit()
                except Exception:
                    # Best-effort upgrade; don't block login.
                    pass

            return dict(user)
        return None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                "SELECT id, email, full_name, role, balance, daily_used, subscription_tier FROM users WHERE lower(email) = lower(?)",
                (_normalize_email(email),),
            )
            user = c.fetchone()
            return dict(user) if user else None

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                "SELECT id, email, full_name, role, balance, daily_used, subscription_tier FROM users WHERE id = ?",
                (user_id,),
            )
            user = c.fetchone()
            return dict(user) if user else None

    async def update_user_role(self, user_id: int, role: str) -> bool:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE users SET role = ? WHERE id = ?",
                (role, user_id),
            )
            conn.commit()
            return c.rowcount > 0

    async def get_all_users(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                "SELECT id, email, full_name, role, balance, daily_used, subscription_tier, created_at FROM users ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in c.fetchall()]

    # ═══════════════════════════════════════════════════════════════
    # 💰 BALANCE & BILLING (Atomic Operations)
    # ═══════════════════════════════════════════════════════════════

    async def get_user_balance(self, user_id: str) -> int:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT balance FROM users WHERE lower(email) = lower(?) OR id = ?",
                (_normalize_email(user_id), user_id),
            )
            result = c.fetchone()
        return result[0] if result else 0

    async def deduct_tokens(
        self, user_id: str, amount: int, tool_name: str = ""
    ) -> bool:
        """Atomic balance deduction — check + deduct in one transaction."""
        with self._get_conn() as conn:
            c = conn.cursor()
            # Atomic: only deduct if balance >= amount
            c.execute(
                """UPDATE users SET balance = balance - ?, daily_used = daily_used + ?
                   WHERE (lower(email) = lower(?) OR id = ?) AND balance >= ?""",
                (amount, amount, _normalize_email(user_id), user_id, amount),
            )
            if c.rowcount == 0:
                return False

            # Log the usage
            if tool_name:
                c.execute(
                    "INSERT INTO usage_logs (user_id, tool_name, tokens_cost, platform) VALUES (?, ?, ?, 'web')",
                    (str(user_id), tool_name, amount),
                )
            conn.commit()
        return True

    async def add_tokens(self, user_id: str, amount: int) -> bool:
        """Add tokens to user balance (after purchase)."""
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE users SET balance = balance + ? WHERE lower(email) = lower(?) OR id = ?",
                (amount, _normalize_email(user_id), user_id),
            )
            conn.commit()
            return c.rowcount > 0

    async def reset_daily_usage(self, user_id: str):
        """Reset daily counter if date changed."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE users SET daily_used = 0, daily_reset_date = ? WHERE (lower(email) = lower(?) OR id = ?) AND (daily_reset_date IS NULL OR daily_reset_date != ?)",
                (today, _normalize_email(user_id), user_id, today),
            )
            conn.commit()

    async def get_daily_usage(self, user_id: str) -> Dict[str, Any]:
        """Get daily usage stats."""
        await self.reset_daily_usage(user_id)
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                "SELECT balance, daily_used, subscription_tier FROM users WHERE lower(email) = lower(?) OR id = ?",
                (_normalize_email(user_id), user_id),
            )
            row = c.fetchone()
            if row:
                tier = row["subscription_tier"] or "free"
                tier_limits = {"free": 50, "pro": 500, "enterprise": -1}
                daily_limit = tier_limits.get(tier, 50)
                return {
                    "balance": row["balance"],
                    "daily_used": row["daily_used"],
                    "daily_limit": daily_limit,
                    "tier": tier,
                    "can_use": daily_limit == -1 or row["daily_used"] < daily_limit,
                }
        return {
            "balance": 0,
            "daily_used": 0,
            "daily_limit": 50,
            "tier": "free",
            "can_use": False,
        }

    async def log_usage(
        self, user_id: str, tool_name: str, tokens: int, summary: str = ""
    ):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO logs (user_id, tool_name, tokens) VALUES (?, ?, ?)",
                (str(user_id), tool_name, tokens),
            )
            conn.commit()

    async def get_usage_history(
        self, user_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                "SELECT tool_name, tokens_cost, timestamp FROM usage_logs WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (str(user_id), limit),
            )
            return [dict(r) for r in c.fetchall()]

    # ═══════════════════════════════════════════════════════════════
    # 🧠 Agent Memory
    # ═══════════════════════════════════════════════════════════════

    async def save_message(self, user_id: int, role: str, content: str):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content),
            )
            conn.commit()

    async def get_recent_messages(
        self, user_id: int, limit: int = 10
    ) -> List[Dict[str, str]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            )
            rows = c.fetchall()
            return [
                {"role": r["role"], "content": r["content"]} for r in reversed(rows)
            ]

    # ═══════════════════════════════════════════════════════════════
    # 🔑 Session Management
    # ═══════════════════════════════════════════════════════════════

    async def create_session(self, user_id: int, token: str, expires_at: str):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
                (user_id, token, expires_at),
            )
            conn.commit()

    async def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM sessions WHERE token = ?", (token,))
            row = c.fetchone()
            return dict(row) if row else None

    async def delete_session(self, token: str):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()

    async def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "DELETE FROM sessions WHERE expires_at < ?",
                (datetime.now().isoformat(),),
            )
            conn.commit()

    # ═══════════════════════════════════════════════════════════════
    # 🔧 Generic Execute (for payment system compatibility)
    # ═══════════════════════════════════════════════════════════════

    async def execute(self, query: str, params: tuple = ()) -> Optional[List[Dict]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                return [dict(row) for row in c.fetchall()]
            conn.commit()
            return None

    # ═══════════════════════════════════════════════════════════════
    # 📲 TELEGRAM VERIFICATION
    # ═══════════════════════════════════════════════════════════════

    async def set_user_verified(self, user_id: int, telegram_chat_id: str = None) -> bool:
        """Mark a user as verified and optionally link their Telegram chat ID."""
        with self._get_conn() as conn:
            c = conn.cursor()
            if telegram_chat_id:
                c.execute(
                    "UPDATE users SET is_verified = 1, telegram_chat_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (telegram_chat_id, user_id),
                )
            else:
                c.execute(
                    "UPDATE users SET is_verified = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (user_id,),
                )
            conn.commit()
            return c.rowcount > 0

    async def store_otp(self, user_id: int, code: str, purpose: str = "telegram_verify", minutes: int = 10):
        """Store an OTP code for a user."""
        expires_at = (datetime.now() + __import__('datetime').timedelta(minutes=minutes)).isoformat()
        with self._get_conn() as conn:
            c = conn.cursor()
            # Invalidate old unused codes for this user + purpose
            c.execute(
                "UPDATE otp_codes SET used = 1 WHERE user_id = ? AND purpose = ? AND used = 0",
                (str(user_id), purpose),
            )
            c.execute(
                "INSERT INTO otp_codes (user_id, code, purpose, expires_at) VALUES (?, ?, ?, ?)",
                (str(user_id), code, purpose, expires_at),
            )
            conn.commit()

    async def verify_otp(self, user_id: int, code: str, purpose: str = "telegram_verify") -> bool:
        """Verify an OTP code. Returns True if valid."""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                "SELECT id FROM otp_codes WHERE user_id = ? AND code = ? AND purpose = ? AND used = 0 AND expires_at > ? ORDER BY id DESC LIMIT 1",
                (str(user_id), code, purpose, now),
            )
            row = c.fetchone()
            if not row:
                return False
            c.execute("UPDATE otp_codes SET used = 1 WHERE id = ?", (row["id"],))
            conn.commit()
            return True

    async def get_user_by_email_unverified(self, email: str) -> Optional[Dict[str, Any]]:
        """Get an unverified user by email (for OTP flow)."""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                "SELECT id, email, full_name, is_verified FROM users WHERE lower(email) = lower(?)",
                (_normalize_email(email),),
            )
            user = c.fetchone()
            return dict(user) if user else None

    # ═══════════════════════════════════════════════════════════════
    # 📊 Admin Stats
    # ═══════════════════════════════════════════════════════════════

    async def get_stats(self) -> Dict[str, Any]:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users")
            total_users = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admins = c.fetchone()[0]
            c.execute("SELECT SUM(balance) FROM users")
            total_balance = c.fetchone()[0] or 0
            c.execute(
                "SELECT COUNT(*) FROM usage_logs WHERE DATE(timestamp) = DATE('now')"
            )
            today_requests = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM usage_logs")
            total_requests = c.fetchone()[0]
        return {
            "total_users": total_users,
            "admins": admins,
            "total_balance": total_balance,
            "today_requests": today_requests,
            "total_requests": total_requests,
        }


db_client = Database()
