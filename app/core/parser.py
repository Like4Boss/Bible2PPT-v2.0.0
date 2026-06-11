import re

class ParserError(ValueError):
    pass

class Parser:
    # Regex description:
    # - ^\s* : leading space
    # - (.+?) : book name (non-greedy, matches letters, numbers, spaces)
    # - \s* : optional spaces
    # - (\d+) : chapter number
    # - \s*:\s* : colon (with optional spacing)
    # - (\d+) : start verse number
    # - (?:\s*-\s*(\d+))? : optional hyphen and end verse number
    # - \s*$ : trailing space and end of string
    REF_REGEX = re.compile(r"^\s*(.+?)\s*(\d+)\s*:\s*(\d+)(?:\s*-\s*(\d+))?\s*$")

    @classmethod
    def parse_single_reference(cls, ref_str: str) -> dict:
        """
        Parses a single reference string (e.g. "Genesis 1:18", "요한일서 2:3-9").
        Returns a dict: {book_name, chapter, start_verse, end_verse}
        Raises ParserError if format is invalid.
        """
        match = cls.REF_REGEX.match(ref_str)
        if not match:
            raise ParserError(f"Invalid reference format: '{ref_str}'")
            
        book_name = match.group(1).strip()
        chapter = int(match.group(2))
        start_verse = int(match.group(3))
        end_verse = int(match.group(4)) if match.group(4) else start_verse
        
        if start_verse <= 0 or chapter <= 0:
            raise ParserError(f"Chapter and verse must be greater than 0: '{ref_str}'")
            
        if end_verse < start_verse:
            raise ParserError(f"End verse cannot be before start verse: '{ref_str}'")
            
        return {
            "book_name": book_name,
            "chapter": chapter,
            "start_verse": start_verse,
            "end_verse": end_verse
        }

    @classmethod
    def parse_input_text(cls, text: str) -> list[dict]:
        """
        Splits input text by lines and then by semicolons.
        Returns a list of parsed dictionaries containing coordinate details and line index.
        Each dictionary contains: {raw, book_name, chapter, start_verse, end_verse, line_num}
        """
        parsed_entries = []
        if not text:
            return parsed_entries
            
        lines = text.splitlines()
        for line_idx, line in enumerate(lines, start=1):
            line_cleaned = line.strip()
            if not line_cleaned:
                continue
                
            # Split by semicolon to support multiple references per line
            parts = [p.strip() for p in line_cleaned.split(";") if p.strip()]
            for part in parts:
                try:
                    parsed = cls.parse_single_reference(part)
                    parsed_entries.append({
                        "raw": part,
                        "book_name": parsed["book_name"],
                        "chapter": parsed["chapter"],
                        "start_verse": parsed["start_verse"],
                        "end_verse": parsed["end_verse"],
                        "line_num": line_idx,
                        "error": None
                    })
                except ParserError as e:
                    parsed_entries.append({
                        "raw": part,
                        "book_name": None,
                        "chapter": 0,
                        "start_verse": 0,
                        "end_verse": 0,
                        "line_num": line_idx,
                        "error": str(e)
                    })
        return parsed_entries
