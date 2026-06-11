import os

class SqliteRepository:
    def __init__(self, connection_pool):
        self.pool = connection_pool
        
    def initialize_database(self, schema_sql_path: str):
        """Initializes the SQLite tables using the DDL schema file."""
        if not os.path.exists(schema_sql_path):
            raise FileNotFoundError(f"Schema SQL file not found: {schema_sql_path}")
            
        with open(schema_sql_path, "r", encoding="utf-8") as f:
            schema_ddl = f.read()
            
        conn = self.pool.get_sqlite_connection()
        try:
            conn.executescript(schema_ddl)
            conn.commit()
        finally:
            conn.close()
            
    def populate_books(self, books: list[dict]):
        """Populates the static list of 66 Bible books."""
        conn = self.pool.get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.executemany(
                """
                INSERT OR REPLACE INTO books (id, name_ko, name_en, abbr_en, abbr_ko)
                VALUES (?, ?, ?, ?, ?)
                """,
                [(b["id"], b["ko"], b["en"], b["abbr"], b["abbr_ko"]) for b in books]
            )
            conn.commit()
        finally:
            conn.close()
            
    def insert_verses_batch(self, verses_batch: list[dict]):
        """
        Inserts a batch of aligned verses into the SQLite database.
        Each item in verses_batch should contain:
        book_id, chapter, verse, ngayok, niv
        """
        conn = self.pool.get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.executemany(
                """
                INSERT OR REPLACE INTO verses (book_id, chapter, verse, ngayok, niv)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        v["book_id"],
                        v["chapter"],
                        v["verse"],
                        v.get("ngayok"),
                        v.get("niv")
                    )
                    for v in verses_batch
                ]
            )
            conn.commit()
        finally:
            conn.close()
