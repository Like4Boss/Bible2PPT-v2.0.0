import os
import sqlite3
import pyodbc

class ConnectionPool:
    def __init__(self, mdb_dir: str, sqlite_path: str):
        self.mdb_dir = os.path.abspath(mdb_dir)
        self.sqlite_path = os.path.abspath(sqlite_path)
        
        # MDB File names mapping
        self.mdb_filenames = {
            "ngayok": "ngayok.mdb",
            "niv": "nivdb.mdb"
        }
        
        self._driver_name = self._find_access_driver()
        
    def _find_access_driver(self) -> str:
        """Finds a compatible Microsoft Access ODBC driver on the system."""
        drivers = pyodbc.drivers()
        for d in drivers:
            if "Microsoft Access Driver (*.mdb" in d:
                return d
        
        # Raise clear message indicating missing driver
        raise RuntimeError(
            "Microsoft Access ODBC driver not found on this system. "
            "Please install the Microsoft Access Database Engine (64-bit to match 64-bit Python).\n"
            f"Available drivers were: {drivers}"
        )
        
    def get_mdb_connection(self, key: str) -> pyodbc.Connection:
        """Returns a connection to the specified MDB database."""
        if key not in self.mdb_filenames:
            raise ValueError(f"Unknown database key: {key}")
            
        filename = self.mdb_filenames[key]
        filepath = os.path.join(self.mdb_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Legacy database file not found: {filepath}")
            
        conn_str = f"DRIVER={{{self._driver_name}}};DBQ={filepath};"
        return pyodbc.connect(conn_str)
        
    def get_sqlite_connection(self) -> sqlite3.Connection:
        """Returns a connection to the unified SQLite database."""
        # Ensure parent directories exist
        os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
        conn = sqlite3.connect(self.sqlite_path)
        # Enable foreign key support
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
        
    def verify_all_files_exist(self):
        """Verifies all input MDB files exist."""
        for key, filename in self.mdb_filenames.items():
            filepath = os.path.join(self.mdb_dir, filename)
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Required source file not found: {filepath}")
