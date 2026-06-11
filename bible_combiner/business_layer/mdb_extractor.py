import re
from database_layer.books_metadata import BOOK_KO_TO_ID

class MdbExtractor:
    def __init__(self, mdb_repository):
        self.repo = mdb_repository
        
    def extract_verses(self, key: str):
        """
        Extracts and parses all verses from the legacy database for key ('kkjv', 'ngayok', 'niv').
        Yields dictionaries with keys: book_id, chapter, verse, text
        """
        for chapter in self.repo.fetch_all_chapters(key):
            book_name = chapter["book"]
            chapter_num = chapter["pchp"]
            raw_content = chapter["content"]
            
            book_id = BOOK_KO_TO_ID.get(book_name)
            if not book_id:
                raise ValueError(f"Unknown book name '{book_name}' in database '{key}'")
                
            if not raw_content or not raw_content.strip():
                # Skip empty chapters
                continue
                
            # Apply patches for known data anomalies
            processed_content = self._apply_patches(key, book_name, chapter_num, raw_content)
            
            # Parse individual verses from the content block
            verses = self._parse_verses_from_text(chapter_num, processed_content)
            for c_num, v_num, v_text in verses:
                yield {
                    "book_id": book_id,
                    "chapter": c_num,
                    "verse": v_num,
                    "text": v_text
                }
                
    def _apply_patches(self, key: str, book_name: str, chapter_num: int, content: str) -> str:
        """Applies hardcoded cleanups to address raw data typos in legacy files."""
        if key == "niv" and book_name == "출애굽기" and chapter_num == 38:
            # Fix Exodus 38 (nivdb.mdb) where verse 29 is split and mislabeled as "38:29" in the middle of verse 24,
            # and real verse 29 text is combined inside verse 28.
            patched = content.replace("was\r\r\n38:29 talents", "was 29 talents")
            patched = patched.replace("make their bands. 29 The bronze from", "make their bands.\r\r\n38:29 The bronze from")
            return patched
            
        return content
        
    def _parse_verses_from_text(self, chapter_num: int, text: str) -> list[tuple[int, int, str]]:
        """
        Parses verses out of chapter text block.
        Uses word boundary \b to avoid overlapping whitespace consumption issues on empty verses.
        """
        pattern = rf"\b({chapter_num}):(\d+)\s+"
        matches = list(re.finditer(pattern, text))
        
        verses = []
        for i, match in enumerate(matches):
            c_num = int(match.group(1))
            v_num = int(match.group(2))
            
            start_idx = match.end()
            end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
            
            verse_text = text[start_idx:end_idx].strip()
            verses.append((c_num, v_num, verse_text))
            
        return verses
