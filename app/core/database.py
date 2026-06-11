import os
import sqlite3

class Database:
    def __init__(self, db_path: str):
        self.db_path = os.path.abspath(db_path)
        
    def get_connection(self) -> sqlite3.Connection:
        """Returns a connection to the SQLite database with foreign key support enabled."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"SQLite database file not found: {self.db_path}")
            
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
