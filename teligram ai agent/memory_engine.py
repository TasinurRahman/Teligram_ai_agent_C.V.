import sqlite3
import logging
import os
import json
import chromadb
from chromadb.config import Settings
import config

logger = logging.getLogger(__name__)

class MemoryEngine:
    """
    Dual-layer Memory System:
    1. Relational DB (SQLite): User roles, rate limits, active chat sessions, admin control.
    2. Vector DB (ChromaDB): Long-term memory embeddings for continuous learning.
    """

    def __init__(self):
        self._init_sqlite()
        self._init_chromadb()

    def _init_sqlite(self):
        self.conn = sqlite3.connect(config.SQLITE_DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()

        # Users table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id TEXT PRIMARY KEY,
                username TEXT,
                role TEXT DEFAULT 'user',
                daily_limit INTEGER DEFAULT 50,
                used_today INTEGER DEFAULT 0,
                is_allowed INTEGER DEFAULT 1
            )
        """)

        # Chat History table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT,
                role TEXT,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Daily Self-Upgrade logs table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_upgrades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT DEFAULT (DATE('now')),
                summary TEXT,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def _init_chromadb(self):
        try:
            self.chroma_client = chromadb.PersistentClient(path=config.CHROMADB_PATH)
            self.memory_collection = self.chroma_client.get_or_create_collection("agent_longterm_memory")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
            self.memory_collection = None

    def is_admin(self, telegram_id: str, username: str = "") -> bool:
        """Determines if the given user is the Supreme Creator / Admin (Tasin)."""
        admin_id_str = str(config.ADMIN_TELEGRAM_ID)
        user_id_str = str(telegram_id)
        u_name = (username or "").lower().strip("@")
        
        return user_id_str in ["6539634793", admin_id_str] or u_name == "ttasin2"

    # --- User Management & Admin Superpowers ---
    def get_or_create_user(self, telegram_id: str, username: str = "") -> dict:
        self.cursor.execute("SELECT telegram_id, username, role, daily_limit, used_today, is_allowed FROM users WHERE telegram_id = ?", (str(telegram_id),))
        row = self.cursor.fetchone()
        
        is_creator = self.is_admin(telegram_id, username)
        role = "admin" if is_creator else "user"
        limit = 999999 if is_creator else config.DEFAULT_DAILY_REQUEST_LIMIT

        if not row:
            self.cursor.execute(
                "INSERT INTO users (telegram_id, username, role, daily_limit, used_today, is_allowed) VALUES (?, ?, ?, ?, ?, ?)",
                (str(telegram_id), username, role, limit, 0, 1)
            )
            self.conn.commit()
            return {"telegram_id": str(telegram_id), "username": username, "role": role, "daily_limit": limit, "used_today": 0, "is_allowed": 1}
        
        # Ensure creator always retains supreme admin role
        if is_creator and (row[2] != "admin" or row[3] < 999999):
            self.cursor.execute("UPDATE users SET role = 'admin', daily_limit = 999999, is_allowed = 1 WHERE telegram_id = ?", (str(telegram_id),))
            self.conn.commit()
            return {"telegram_id": row[0], "username": row[1], "role": "admin", "daily_limit": 999999, "used_today": row[4], "is_allowed": 1}

        return {"telegram_id": row[0], "username": row[1], "role": row[2], "daily_limit": row[3], "used_today": row[4], "is_allowed": row[5]}

    def update_user_limit(self, telegram_id: str, new_limit: int):
        self.cursor.execute("UPDATE users SET daily_limit = ? WHERE telegram_id = ?", (new_limit, str(telegram_id)))
        self.conn.commit()

    def ban_user(self, telegram_id: str):
        self.cursor.execute("UPDATE users SET is_allowed = 0 WHERE telegram_id = ?", (str(telegram_id),))
        self.conn.commit()

    def unban_user(self, telegram_id: str):
        self.cursor.execute("UPDATE users SET is_allowed = 1 WHERE telegram_id = ?", (str(telegram_id),))
        self.conn.commit()

    def list_all_users(self) -> list:
        self.cursor.execute("SELECT telegram_id, username, role, daily_limit, used_today, is_allowed FROM users ORDER BY used_today DESC")
        return self.cursor.fetchall()

    def get_system_stats(self) -> dict:
        self.cursor.execute("SELECT COUNT(*) FROM users")
        total_users = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT SUM(used_today) FROM users")
        total_msgs = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_allowed = 0")
        banned_users = self.cursor.fetchone()[0]
        return {
            "total_users": total_users,
            "total_requests_today": total_msgs,
            "banned_users": banned_users
        }

    def reset_daily_limits(self):
        """Resets daily usage counter at midnight."""
        self.cursor.execute("UPDATE users SET used_today = 0")
        self.conn.commit()

    def increment_user_usage(self, telegram_id: str):
        self.cursor.execute("UPDATE users SET used_today = used_today + 1 WHERE telegram_id = ?", (str(telegram_id),))
        self.conn.commit()

    # --- Self-Upgrade Records ---
    def record_self_upgrade(self, summary: str, details: str):
        self.cursor.execute("INSERT INTO daily_upgrades (summary, details) VALUES (?, ?)", (summary, details))
        self.conn.commit()

    def get_latest_self_upgrade(self) -> dict:
        self.cursor.execute("SELECT date, summary, details, created_at FROM daily_upgrades ORDER BY id DESC LIMIT 1")
        row = self.cursor.fetchone()
        if row:
            return {"date": row[0], "summary": row[1], "details": row[2], "created_at": row[3]}
        return None

    # --- Conversation History ---
    def add_chat_message(self, telegram_id: str, role: str, message: str):
        self.cursor.execute("INSERT INTO chat_history (telegram_id, role, message) VALUES (?, ?, ?)", (str(telegram_id), role, message))
        self.conn.commit()

        # Vector memory
        if role == "user" and self.memory_collection and len(message) > 15:
            try:
                self.memory_collection.add(
                    documents=[message],
                    metadatas=[{"telegram_id": str(telegram_id)}],
                    ids=[f"msg_{telegram_id}_{os.urandom(4).hex()}"]
                )
            except Exception as e:
                logger.warning(f"Could not store vector memory: {e}")

    def get_chat_history(self, telegram_id: str, limit: int = 10) -> list:
        self.cursor.execute(
            "SELECT role, message FROM chat_history WHERE telegram_id = ? ORDER BY id DESC LIMIT ?",
            (str(telegram_id), limit)
        )
        rows = self.cursor.fetchall()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def search_vector_memory(self, query: str, telegram_id: str, n_results: int = 3) -> list:
        if not self.memory_collection:
            return []
        try:
            results = self.memory_collection.query(
                query_texts=[query],
                where={"telegram_id": str(telegram_id)},
                n_results=n_results
            )
            return results.get("documents", [[]])[0]
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []
