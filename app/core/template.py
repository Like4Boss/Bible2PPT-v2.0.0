class Template:
    def __init__(self):
        # Text positioning and sizes
        self.verse_location = "top"     # top, center, bottom
        self.ref_location = "top"          # top, bottom
        self.alignment = "left"          # left, center, right
        
        # Font settings
        self.font_ko = "Malgun Gothic"
        self.font_en = "Arial"
        self.font_size_ko = 32
        self.font_size_en = 32
        
        # Color settings (Hex strings)
        self.font_color = "#FFFFFF"        # White font
        self.bg_color = "#2d2d2d"          # Dark background
        
        # Layout behaviors
        self.split_verses = True           # True: One slide per verse; False: Combine range on one slide
        self.bilingual_order = "ko_en"     # ko_en, en_ko, ko_only, en_only
        self.ref_order = "ko_en"           # ko_en (Korean - English), en_ko (English - Korean)
        self.line_spacing = 1.3            # Spacing between paragraphs
        
    def to_dict(self) -> dict:
        return self.__dict__.copy()
        
    def from_dict(self, data: dict):
        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, v)
