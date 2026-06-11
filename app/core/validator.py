class Validator:
    def __init__(self, repository):
        self.repo = repository
        self.books = self.repo.get_books()
        self._build_mappings()
        
    def _build_mappings(self):
        # Build a case-insensitive lookup mapping for all possible book names/abbreviations
        self.name_map = {}
        for b in self.books:
            # Add all names/abbreviations to lookup mapping
            keys = [
                b["name_ko"].lower(),
                b["name_en"].lower(),
                b["abbr_en"].lower(),
                b["abbr_ko"].lower()
            ]
            for k in keys:
                if k:
                    self.name_map[k] = b

    def validate_reference(self, parsed_ref: dict) -> dict:
        """
        Validates the parsed reference against database constraints.
        Returns a dict: {valid: bool, description: str, book_id: int}
        """
        if parsed_ref.get("error"):
            return {
                "valid": False,
                "description": f"Error: {parsed_ref['error']}",
                "book_id": 0
            }
            
        book_name = parsed_ref["book_name"]
        chapter = parsed_ref["chapter"]
        start_verse = parsed_ref["start_verse"]
        end_verse = parsed_ref["end_verse"]
        
        # 1. Resolve book
        book = self.name_map.get(book_name.lower())
        if not book:
            return {
                "valid": False,
                "description": f"Error: Book '{book_name}' not found.",
                "book_id": 0
            }
            
        book_id = book["id"]
        book_display = f"{book['name_en']} ({book['name_ko']})"
        
        # 2. Check chapter count
        max_chapters = self.repo.get_chapter_count(book_id)
        if chapter > max_chapters:
            return {
                "valid": False,
                "description": f"Error: {book['name_en']} only has {max_chapters} chapters.",
                "book_id": book_id
            }
            
        # 3. Check verse range count
        max_verses = self.repo.get_verse_count(book_id, chapter)
        if start_verse > max_verses:
            return {
                "valid": False,
                "description": f"Error: {book['name_en']} Chapter {chapter} only has {max_verses} verses.",
                "book_id": book_id
            }
            
        if end_verse > max_verses:
            return {
                "valid": False,
                "description": f"Error: {book['name_en']} Chapter {chapter} only has {max_verses} verses (requested verse {end_verse} exceeds bounds).",
                "book_id": book_id
            }
            
        # 4. Success Description
        verse_desc = f"Verse {start_verse}" if start_verse == end_verse else f"Verses {start_verse} through {end_verse}"
        description = f"Valid: {book_display}, Chapter {chapter}, {verse_desc}."
        
        return {
            "valid": True,
            "description": description,
            "book_id": book_id
        }
