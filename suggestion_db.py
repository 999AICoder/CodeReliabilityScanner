import sqlite3
import os
import sys
from typing import List, Dict
import json
from datetime import datetime

class SuggestionDB:
    def __init__(self, db_path: str = "suggestions.db"):
        # Use in-memory database for testing
        if 'pytest' in sys.modules:
            db_path = ':memory:'
        else:
            # Ensure the database directory exists
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
        self.db_path = db_path
        # Create tables immediately
        with sqlite3.connect(self.db_path) as conn:
            self._create_table(conn)

    def _create_table(self, conn):
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

    def add_suggestion(self, file: str, question: str, response: Dict, model: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO suggestions (file, question, response, model, timestamp) VALUES (?, ?, ?, ?, ?)",
                (file, question, json.dumps(response), model, datetime.now().isoformat())
            )

    def get_suggestions(self, file: str = None) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
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
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM suggestions WHERE id = ?", (suggestion_id,))
            row = cursor.fetchone()
            if row:
                suggestion = dict(row)
                suggestion['response'] = json.loads(suggestion['response'])
                return suggestion
            return None

    def update_suggestion(self, suggestion_id: int, response: Dict):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE suggestions SET response = ? WHERE id = ?",
                (json.dumps(response), suggestion_id)
            )

    def delete_suggestion(self, suggestion_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM suggestions WHERE id = ?", (suggestion_id,))
