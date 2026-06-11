import sqlite3

class Repository:
    def __init__(self, database):
        self.db = database
        
    def get_books(self) -> list[dict]:
        """Fetches the static list of all 66 books from the database."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, name_ko, name_en, abbr_en, abbr_ko 
                FROM books 
                ORDER BY id
                """
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "name_ko": r[1],
                    "name_en": r[2],
                    "abbr_en": r[3],
                    "abbr_ko": r[4]
                }
                for r in rows
            ]
        finally:
            conn.close()
            
    def get_chapter_count(self, book_id: int) -> int:
        """Returns the maximum chapter number for the given book."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT MAX(chapter) FROM verses WHERE book_id = ?",
                (book_id,)
            )
            val = cursor.fetchone()[0]
            return val if val is not None else 0
        finally:
            conn.close()
            
    def get_verse_count(self, book_id: int, chapter: int) -> int:
        """Returns the maximum verse number in the given book and chapter."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT MAX(verse) FROM verses WHERE book_id = ? AND chapter = ?",
                (book_id, chapter)
            )
            val = cursor.fetchone()[0]
            return val if val is not None else 0
        finally:
            conn.close()
            
    def get_verses(self, book_id: int, chapter: int, start_verse: int, end_verse: int) -> list[dict]:
        """
        Fetches aligned verses for a book, chapter, and verse range.
        Returns a list of dicts: [ {book_id, chapter, verse, ngayok, niv}, ... ]
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT book_id, chapter, verse, ngayok, niv 
                FROM verses 
                WHERE book_id = ? AND chapter = ? AND verse BETWEEN ? AND ?
                ORDER BY verse
                """,
                (book_id, chapter, start_verse, end_verse)
            )
            rows = cursor.fetchall()
            return [
                {
                    "book_id": r[0],
                    "chapter": r[1],
                    "verse": r[2],
                    "ngayok": r[3],
                    "niv": r[4]
                }
                for r in rows
            ]
        finally:
            conn.close()
