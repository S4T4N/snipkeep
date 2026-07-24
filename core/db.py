# core/db.py
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from utils.helpers import get_data_dir

class SnipDB:
    def __init__(self):
        self.db_path = get_data_dir() / "snipkeep.db"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS snippets (
                id TEXT PRIMARY KEY,
                code TEXT NOT NULL,
                language TEXT,
                description TEXT,
                tags TEXT,
                source TEXT,
                file_path TEXT,
                embedding BLOB,
                created_at TEXT,
                updated_at TEXT,
                run_count INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def add_snippet(self, code, language=None, description="", tags="", source="manual", file_path=""):
        snip_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        self.conn.execute("""
            INSERT INTO snippets (id, code, language, description, tags, source, file_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (snip_id, code, language, description, tags, source, file_path, now, now))
        self.conn.commit()
        return snip_id

    def get_all_snippets(self):
        cursor = self.conn.execute("SELECT * FROM snippets ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def get_snippet_by_id(self, snip_id):
        cursor = self.conn.execute("SELECT * FROM snippets WHERE id = ?", (snip_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_embedding(self, snip_id, embedding):
        self.conn.execute("UPDATE snippets SET embedding = ? WHERE id = ?", (embedding, snip_id))
        self.conn.commit()

    def update_description(self, snip_id, description):
        now = datetime.now().isoformat()
        self.conn.execute("UPDATE snippets SET description = ?, updated_at = ? WHERE id = ?",
                          (description, now, snip_id))
        self.conn.commit()

    def delete_snippet(self, snip_id):
        self.conn.execute("DELETE FROM snippets WHERE id = ?", (snip_id,))
        self.conn.commit()

    def increment_run_count(self, snip_id):
        self.conn.execute("UPDATE snippets SET run_count = run_count + 1 WHERE id = ?", (snip_id,))
        self.conn.commit()

    def search_by_text(self, query):
        cursor = self.conn.execute("""
            SELECT * FROM snippets 
            WHERE code LIKE ? OR description LIKE ? OR tags LIKE ?
            ORDER BY created_at DESC
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        return [dict(row) for row in cursor.fetchall()]
