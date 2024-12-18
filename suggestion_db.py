import sqlite3
import os
import sys
from typing import List, Dict
import json
from datetime import datetime
from logger import Logger

class SuggestionDB:
    """A simple SQLite database wrapper for storing code suggestions."""
    def __init__(self, db_path: str = "suggestions.db", force_file: bool = False):
        self.logger = Logger()
        self.logger.info(f"Initializing SuggestionDB with path: {db_path}")
        self.db_path = db_path if force_file else (':memory:' if 'pytest' in sys.modules else db_path)
        
        # Create db directory if needed
        if self.db_path != ':memory:':
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)

        # Initialize connection
        self._conn = None
        self._initialize_db()

    def __enter__(self):
        """Context manager entry point."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point - ensure proper cleanup."""
        if self._conn:
            try:
                if exc_type is None:  # No exception occurred
                    self._conn.commit()
                else:
                    self._conn.rollback()
            finally:
                self._conn.close()
                self._conn = None

    def _initialize_db(self):
        """Initialize database connection and create table if needed."""
        self.logger.info(f"Initializing database connection to: {self.db_path}")
        self._conn = sqlite3.connect(
            self.db_path,
            timeout=30,
            isolation_level=None,  # Enable autocommit mode
            check_same_thread=False
        )
        
        # Set pragmas for better reliability
        self._conn.execute('PRAGMA journal_mode=WAL')
        self._conn.execute('PRAGMA synchronous=NORMAL')
        self._conn.execute('PRAGMA foreign_keys=ON')
        self._conn.execute('PRAGMA temp_store=MEMORY')
        self._conn.row_factory = sqlite3.Row

        try:
            self.logger.info("Creating database table if needed")
            cursor = self._conn.cursor()
            self.logger.info(f"Executing CREATE TABLE SQL: {self.CREATE_TABLE_SQL}")
            cursor.execute(self.CREATE_TABLE_SQL)
            self.logger.info("Verifying table creation")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suggestions'")
            result = cursor.fetchone()
            self.logger.info(f"Table verification result: {result}")
            if not result:
                self.logger.error("Failed to create suggestions table")
                raise sqlite3.OperationalError("Failed to create suggestions table")
            self._conn.commit()
            self.logger.info("Table creation successful")
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
            raise

    def __del__(self):
        """Cleanup database connection when object is destroyed."""
        if hasattr(self, '_conn') and self._conn:
            try:
                self._conn.close()
            except Exception as e:
                self.logger.error(f"Error closing database connection: {e}")

    def _get_connection(self):
        """Get a database connection, reconnecting if needed."""
        if not self._conn:
            self._initialize_db()
            # Enable WAL mode for better concurrency
            self._conn.execute('PRAGMA journal_mode=WAL')
            # Enable foreign keys
            self._conn.execute('PRAGMA foreign_keys=ON')
        return self._conn

    def _verify_table(self, conn):
        """Verify that the suggestions table exists."""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='suggestions'"
        )
        if not cursor.fetchone():
            raise sqlite3.OperationalError("Failed to create suggestions table")

    # SQL for creating the suggestions table
    CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file TEXT NOT NULL,
            question TEXT NOT NULL,
            response JSON NOT NULL,
            model TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    """

    def _create_table(self, conn):
        """Create the suggestions table if it doesn't exist."""
        try:
            cursor = conn.cursor()
            cursor.execute(self.CREATE_TABLE_SQL)
            cursor.close()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
            raise sqlite3.OperationalError(f"Failed to create suggestions table: {e}")

    def add_suggestion(self, file: str, question: str, response: Dict, model: str):
        self.logger.info(f"Adding suggestion for file: {file}")
        conn = self._get_connection()
        try:
            conn.execute(
                "INSERT INTO suggestions (file, question, response, model, timestamp) VALUES (?, ?, ?, ?, ?)",
                (file, question, json.dumps(response), model, datetime.now().isoformat())
            )
            conn.commit()
            self.logger.info("Successfully added suggestion")
        except sqlite3.Error as e:
            self.logger.error(f"Error adding suggestion: {e}")
            conn.rollback()
            raise

    def get_suggestions(self, file: str = None) -> List[Dict]:
        conn = self._get_connection()
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
