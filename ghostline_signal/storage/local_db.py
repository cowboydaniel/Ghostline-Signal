"""
Local message storage for Ghostline Signal.
All messages are stored locally with no cloud sync.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class MessageStore:
    """Local storage for messages."""

    def __init__(self, storage_path: str = None):
        """Initialize message store."""
        if storage_path is None:
            storage_path = Path.home() / '.ghostline_signal' / 'messages.db'
        else:
            storage_path = Path(storage_path)

        storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = storage_path
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                peer_id TEXT NOT NULL,
                content BLOB NOT NULL,
                timestamp REAL NOT NULL,
                direction TEXT NOT NULL,
                session_id TEXT,
                delivered INTEGER DEFAULT 0
            )
        ''')

        # Peers table (device identities)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS peers (
                peer_id TEXT PRIMARY KEY,
                display_name TEXT,
                public_key BLOB NOT NULL,
                first_seen REAL NOT NULL,
                last_seen REAL,
                trust_level INTEGER DEFAULT 0
            )
        ''')

        # Sessions table (ephemeral session keys)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                peer_id TEXT NOT NULL,
                session_key BLOB NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                FOREIGN KEY (peer_id) REFERENCES peers (peer_id)
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_peer ON messages(peer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_peer ON sessions(peer_id)')

        conn.commit()
        conn.close()

    def store_message(self, peer_id: str, content: bytes, direction: str,
                     session_id: str = None, delivered: bool = False) -> int:
        """
        Store a message.
        direction: 'sent' or 'received'
        Returns message ID.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        timestamp = datetime.now().timestamp()

        cursor.execute('''
            INSERT INTO messages (peer_id, content, timestamp, direction, session_id, delivered)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (peer_id, content, timestamp, direction, session_id, 1 if delivered else 0))

        message_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return message_id

    def get_messages(self, peer_id: str, limit: int = 100) -> List[Dict]:
        """Get messages for a specific peer."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, content, timestamp, direction, session_id, delivered
            FROM messages
            WHERE peer_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (peer_id, limit))

        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row[0],
                'content': row[1],
                'timestamp': row[2],
                'direction': row[3],
                'session_id': row[4],
                'delivered': bool(row[5])
            })

        conn.close()
        return list(reversed(messages))  # Return in chronological order

    def add_peer(self, peer_id: str, public_key: bytes, display_name: str = None,
                 trust_level: int = 0):
        """Add or update a peer."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        timestamp = datetime.now().timestamp()

        cursor.execute('''
            INSERT OR REPLACE INTO peers (peer_id, display_name, public_key, first_seen, last_seen, trust_level)
            VALUES (?, ?, ?,
                COALESCE((SELECT first_seen FROM peers WHERE peer_id = ?), ?),
                ?, ?)
        ''', (peer_id, display_name, public_key, peer_id, timestamp, timestamp, trust_level))

        conn.commit()
        conn.close()

    def get_peer(self, peer_id: str) -> Optional[Dict]:
        """Get peer information."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT peer_id, display_name, public_key, first_seen, last_seen, trust_level
            FROM peers
            WHERE peer_id = ?
        ''', (peer_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'peer_id': row[0],
                'display_name': row[1],
                'public_key': row[2],
                'first_seen': row[3],
                'last_seen': row[4],
                'trust_level': row[5]
            }
        return None

    def get_all_peers(self) -> List[Dict]:
        """Get all known peers."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT peer_id, display_name, public_key, first_seen, last_seen, trust_level
            FROM peers
            ORDER BY last_seen DESC
        ''')

        peers = []
        for row in cursor.fetchall():
            peers.append({
                'peer_id': row[0],
                'display_name': row[1],
                'public_key': row[2],
                'first_seen': row[3],
                'last_seen': row[4],
                'trust_level': row[5]
            })

        conn.close()
        return peers

    def store_session(self, session_id: str, peer_id: str, session_key: bytes,
                     expires_at: float):
        """Store an ephemeral session key."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        created_at = datetime.now().timestamp()

        cursor.execute('''
            INSERT OR REPLACE INTO sessions (session_id, peer_id, session_key, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, peer_id, session_key, created_at, expires_at))

        conn.commit()
        conn.close()

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session information."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT session_id, peer_id, session_key, created_at, expires_at
            FROM sessions
            WHERE session_id = ?
        ''', (session_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'session_id': row[0],
                'peer_id': row[1],
                'session_key': row[2],
                'created_at': row[3],
                'expires_at': row[4]
            }
        return None

    def cleanup_expired_sessions(self):
        """Remove expired session keys."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        now = datetime.now().timestamp()
        cursor.execute('DELETE FROM sessions WHERE expires_at < ?', (now,))

        conn.commit()
        conn.close()

    def update_peer_last_seen(self, peer_id: str):
        """Update last seen timestamp for a peer."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        timestamp = datetime.now().timestamp()
        cursor.execute('UPDATE peers SET last_seen = ? WHERE peer_id = ?', (timestamp, peer_id))

        conn.commit()
        conn.close()
