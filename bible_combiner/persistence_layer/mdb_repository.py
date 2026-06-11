class MdbRepository:
    def __init__(self, connection_pool):
        self.pool = connection_pool
        
    def fetch_all_chapters(self, key: str):
        """
        Generates dictionary rows representing chapters from the MDB database.
        Columns returned: code, book, pchp, tchp, content
        """
        conn = self.pool.get_mdb_connection(key)
        cursor = conn.cursor()
        
        # Dynamically determine the user table name
        tables = [row.table_name for row in cursor.tables() if row.table_type == 'TABLE']
        if not tables:
            conn.close()
            raise RuntimeError(f"No user tables found in MDB database for key: {key}")
        table_name = tables[0]
        
        # Fetch columns in a standardized order, sorted by CODE (sequential chapters)
        cursor.execute(f"SELECT CODE, BOOK, PCHP, TCHP, CONTENT FROM [{table_name}] ORDER BY CODE")
        
        try:
            while True:
                row = cursor.fetchone()
                if not row:
                    break
                yield {
                    "code": row[0],
                    "book": row[1],
                    "pchp": row[2],
                    "tchp": row[3],
                    "content": row[4]
                }
        finally:
            cursor.close()
            conn.close()
