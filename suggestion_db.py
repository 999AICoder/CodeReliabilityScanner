import sqlite3
import os
import sys
from typing import List, Dict
import json
from datetime import datetime

class SuggestionDB:
    def __init__(self, db_path: str = "suggestions.db"):
        self.db_path = ':memory:' if 'pytest' in sys.modules else db_path
        if self.db_path != ':memory:':
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
        
        # Initialize database
        with self._get_connection() as conn:
            self._create_table(conn)
            self._verify_table(conn)

    def _get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def _verify_table(self, conn):
        """Verify that the suggestions table exists."""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='suggestions'"
        )
        if not cursor.fetchone():
            raise sqlite3.OperationalError("Failed to create suggestions table")

    def _create_table(self, conn):
        """Create the suggestions table if it doesn't exist."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file TEXT NOT NULL,
                question TEXT NOT NULL,
                response JSON NOT NULL,
                model TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            )
        """)
        conn.commit()

    def add_suggestion(self, file: str, question: str, response: Dict, model: str):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO suggestions (file, question, response, model, timestamp) VALUES (?, ?, ?, ?, ?)",
                (file, question, json.dumps(response), model, datetime.now().isoformat())
            )

    def get_suggestions(self, file: str = None) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            if file:
                cursor = conn.execute(
                    "SELECT * FROM suggestions WHERE file = ? ORDER BY timestamp DESC",
                    (file,)
                )
            else:
                cursor = conn.execute("SELECT * FROM suggestions ORDER BY timestamp DESC")
            
            results = []
            for row in cursor.fetchall():
                suggestion = dict(row)
                suggestion['response'] = json.loads(suggestion['response'])
                results.append(suggestion)
            return results

    def get_suggestion(self, suggestion_id: int) -> Dict:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM suggestions WHERE id = ?", (suggestion_id,))
            row = cursor.fetchone()
            if row:
                suggestion = dict(row)
                suggestion['response'] = json.loads(suggestion['response'])
                return suggestion
            return None

    def update_suggestion(self, suggestion_id: int, response: Dict):
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE suggestions SET response = ? WHERE id = ?",
                (json.dumps(response), suggestion_id)
            )

    def delete_suggestion(self, suggestion_id: int):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM suggestions WHERE id = ?", (suggestion_id,))
