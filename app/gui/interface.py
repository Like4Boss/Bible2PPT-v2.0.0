import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import queue

from core.parser import Parser
from core.validator import Validator
from core.template import Template
from core.ppt_compiler import PPTCompiler

class Interface(tk.Frame):
    def __init__(self, parent, repository, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.repo = repository
        
        # Instantiate business objects
        self.validator = Validator(self.repo)
        self.compiler = PPTCompiler(self.repo)
        self.template = Template()
        
        # UI State variables
        self.validation_queue = queue.Queue()
        self.validation_timer = None
        self.is_valid = False
        self.parsed_entries = []
        
        # Dynamic cache for dropdowns
        self.books = self.repo.get_books()
        self.book_by_name = {b["name_ko"]: b for b in self.books}
        
        # Configure overall style
        self._configure_styles()
        
        # Build UI layout
        self._create_widgets()
        
        # Load settings from template object to UI
        self._load_template_to_ui()
        
        # Run initial UI checks
        self._update_picker_chapters()
        self._trigger_async_validation()
        
        # Queue check polling
        self._poll_validation_queue()

    def _configure_styles(self):
        """Sets up a modern, dark, flat theme styling for ttk widgets."""
        self.bg_dark = "#1e1e1e"      # Deep charcoal background
        self.bg_panel = "#2d2d2d"     # Panel background
        self.fg_white = "#ffffff"     # White text
        self.accent_blue = "#007acc"  # VS Code Blue accent
        
        # Standard configuration of the Tk parent window
        self.parent.configure(bg=self.bg_dark)
        
        style = ttk.Style()
        style.theme_use("clam")
        
        # Dark panel style
        style.configure("TFrame", background=self.bg_dark)
        style.configure("Panel.TFrame", background=self.bg_panel)
        
        # Custom Label Styles
        style.configure("TLabel", background=self.bg_dark, foreground=self.fg_white, font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background=self.bg_panel, foreground=self.fg_white, font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=self.bg_panel, foreground=self.accent_blue, font=("Segoe UI", 12, "bold"))
        style.configure("Title.TLabel", background=self.bg_dark, foreground=self.accent_blue, font=("Segoe UI", 16, "bold"))
        
        # Custom Button Style
        style.configure("TButton", background=self.accent_blue, foreground=self.fg_white, font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("TButton",
                  background=[("active", "#0098ff"), ("disabled", "#555555")],
                  foreground=[("disabled", "#aaaaaa")])
                  
        # Checkbox & Combobox Styles
        style.configure("TCheckbutton", background=self.bg_panel, foreground=self.fg_white, font=("Segoe UI", 10))
        
        # Configure Combobox style for dark theme
        style.configure("TCombobox", 
                        background=self.bg_panel, 
                        foreground=self.fg_white, 
                        fieldbackground="#2d2d2d", 
                        arrowcolor=self.fg_white,
                        borderwidth=1,
                        relief="flat")
                        
        style.map("TCombobox",
                  fieldbackground=[("readonly", "#2d2d2d"), ("disabled", "#2d2d2d"), ("focus", "#2d2d2d")],
                  foreground=[("readonly", self.fg_white), ("disabled", "#888888"), ("focus", self.fg_white)],
                  background=[("readonly", self.bg_panel), ("disabled", "#222222"), ("focus", self.bg_panel)],
                  arrowcolor=[("readonly", self.fg_white), ("disabled", "#888888"), ("focus", self.fg_white)])
                  
        # Style the dropdown Listbox popdown for Comboboxes
        self.option_add("*TCombobox*Listbox.background", "#1e1e1e")
        self.option_add("*TCombobox*Listbox.foreground", self.fg_white)
        self.option_add("*TCombobox*Listbox.selectBackground", self.accent_blue)
        self.option_add("*TCombobox*Listbox.selectForeground", self.fg_white)
        self.option_add("*TCombobox*Listbox.font", ("Segoe UI", 10))

    def _create_widgets(self):
        # 1. Main Title
        title_lbl = ttk.Label(self, text="Bible2PPT - Bilingual Presentation Compiler", style="Title.TLabel")
        title_lbl.pack(anchor="w", pady=(10, 20), padx=10)
        
        # Main split container (Left: Text Inputs & Logs, Right: Helper & Templates)
        main_container = ttk.Frame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        left_pane = ttk.Frame(main_container)
        left_pane.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right_pane = ttk.Frame(main_container, width=320)
        right_pane.pack(side="right", fill="both", expand=False)
        right_pane.pack_propagate(False)
        
        # ==================== LEFT PANE (Reference input & Verification) ====================
        
        # Reference Text input area
        input_header_frame = ttk.Frame(left_pane)
        input_header_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(input_header_frame, text="Input Bible References (separated by semicolons or newlines):", font=("Segoe UI", 10, "bold")).pack(side="left")
        
        self.ref_text = tk.Text(
            left_pane,
            wrap="word",
            bg="#252526",
            fg="#cccccc",
            insertbackground="#ffffff",
            font=("Consolas", 11),
            height=12,
            bd=1,
            relief="flat",
            padx=8,
            pady=8
        )
        self.ref_text.pack(fill="both", expand=True)
        
        # Prepopulate with a helpful example
        self.ref_text.insert("1.0", "요한일서 2:3-9;\n창세기 1:1; Genesis 1:18; 1 John 2:3-99\n")
        
        # Setup tagging configuration in Text editor
        self.ref_text.tag_configure("valid_line", background="#1e3f20", foreground="#a6e22e")
        self.ref_text.tag_configure("invalid_line", background="#3f1e1e", foreground="#f92672")
        
        # Bind events for live validation
        self.ref_text.bind("<KeyRelease>", self._on_key_release)
        self.ref_text.bind("<FocusOut>", lambda e: self._trigger_async_validation())
        
        # Verification Output / Log area
        log_header = ttk.Label(left_pane, text="Verification Details:", font=("Segoe UI", 10, "bold"))
        log_header.pack(anchor="w", pady=(15, 5))
        
        self.log_text = tk.Text(
            left_pane,
            wrap="word",
            bg="#1e1e1e",
            fg="#888888",
            font=("Segoe UI", 9),
            height=6,
            bd=0,
            relief="flat",
            state="disabled"
        )
        self.log_text.pack(fill="x", pady=(0, 10))
        
        # ==================== RIGHT PANE (Picker & Template Controls) ====================
        
        # Helper picker (Top)
        picker_panel = ttk.Frame(right_pane, style="Panel.TFrame", padding=12)
        picker_panel.pack(fill="x", pady=(0, 15))
        
        ttk.Label(picker_panel, text="Reference Helper Picker", style="Header.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))
        
        # Book
        ttk.Label(picker_panel, text="Book", style="Panel.TLabel").grid(row=1, column=0, sticky="w", pady=2)
        self.pick_book = ttk.Combobox(picker_panel, values=[b["name_ko"] for b in self.books], state="readonly", width=12)
        self.pick_book.set(self.books[0]["name_ko"])
        self.pick_book.grid(row=2, column=0, sticky="w", padx=(0, 4), pady=(0, 8))
        self.pick_book.bind("<<ComboboxSelected>>", lambda e: self._update_picker_chapters())
        
        # Chapter
        ttk.Label(picker_panel, text="Chapter", style="Panel.TLabel").grid(row=1, column=1, sticky="w", pady=2)
        self.pick_chapter = ttk.Combobox(picker_panel, state="readonly", width=6)
        self.pick_chapter.grid(row=2, column=1, sticky="w", padx=(0, 4), pady=(0, 8))
        self.pick_chapter.bind("<<ComboboxSelected>>", lambda e: self._update_picker_verses())
        
        # Start Verse
        ttk.Label(picker_panel, text="Start V", style="Panel.TLabel").grid(row=1, column=2, sticky="w", pady=2)
        self.pick_start = ttk.Combobox(picker_panel, state="readonly", width=5)
        self.pick_start.grid(row=2, column=2, sticky="w", padx=(0, 4), pady=(0, 8))
        self.pick_start.bind("<<ComboboxSelected>>", lambda e: self._sync_picker_end_verse())
        
        # End Verse
        ttk.Label(picker_panel, text="End V", style="Panel.TLabel").grid(row=1, column=3, sticky="w", pady=2)
        self.pick_end = ttk.Combobox(picker_panel, state="readonly", width=5)
        self.pick_end.grid(row=2, column=3, sticky="w", pady=(0, 8))
        
        # Add Reference Button
        add_btn = ttk.Button(picker_panel, text="Insert Reference", command=self._add_picker_reference)
        add_btn.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(5, 0))
        
        # Template Panel (Bottom)
        template_panel = ttk.Frame(right_pane, style="Panel.TFrame", padding=12)
        template_panel.pack(fill="both", expand=True)
        
        ttk.Label(template_panel, text="Slide Design & Layout Settings", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Color Map definition for display conversions
        self.color_map = {
            "White": "#FFFFFF",
            "Black": "#000000",
            "Charcoal": "#121212",
            "Gold": "#FFD700",
            "Gray": "#888888",
            "Light Gray": "#CCCCCC",
            "Dark Gray": "#333333",
            "Blue": "#007ACC",
            "Green": "#A6E22E",
            "Red": "#FF0000"
        }
        self.color_names = list(self.color_map.keys())
        
        # Language Mode
        ttk.Label(template_panel, text="Bilingual / Mode", style="Panel.TLabel").grid(row=1, column=0, sticky="w", pady=2)
        self.temp_mode = ttk.Combobox(template_panel, values=["Korean + English", "English + Korean", "Korean only", "English only"], state="readonly", width=16)
        self.temp_mode.grid(row=1, column=1, sticky="w", pady=2)
        
        # Ref Order (Korean - English / English - Korean)
        ttk.Label(template_panel, text="Ref Order", style="Panel.TLabel").grid(row=2, column=0, sticky="w", pady=2)
        self.temp_ref_order = ttk.Combobox(template_panel, values=["English - Korean", "Korean - English"], state="readonly", width=16)
        self.temp_ref_order.grid(row=2, column=1, sticky="w", pady=2)
        
        # Text Positions
        ttk.Label(template_panel, text="Verse Alignment", style="Panel.TLabel").grid(row=3, column=0, sticky="w", pady=2)
        self.temp_v_loc = ttk.Combobox(template_panel, values=["top", "center", "bottom"], state="readonly", width=10)
        self.temp_v_loc.grid(row=3, column=1, sticky="w", pady=2)
        
        # Ref Position
        ttk.Label(template_panel, text="Ref Alignment", style="Panel.TLabel").grid(row=4, column=0, sticky="w", pady=2)
        self.temp_ref_loc = ttk.Combobox(template_panel, values=["top", "bottom"], state="readonly", width=10)
        self.temp_ref_loc.grid(row=4, column=1, sticky="w", pady=2)
        
        # Alignment
        ttk.Label(template_panel, text="Horiz Align", style="Panel.TLabel").grid(row=5, column=0, sticky="w", pady=2)
        self.temp_align = ttk.Combobox(template_panel, values=["left", "center", "right"], state="readonly", width=10)
        self.temp_align.grid(row=5, column=1, sticky="w", pady=2)
        
        # Fonts
        ttk.Label(template_panel, text="Korean Font", style="Panel.TLabel").grid(row=6, column=0, sticky="w", pady=2)
        self.temp_font_ko = ttk.Combobox(template_panel, values=["Malgun Gothic", "NanumGothic", "맑은 고딕", "굴림", "바탕"], state="normal", width=14)
        self.temp_font_ko.grid(row=6, column=1, sticky="w", pady=2)
        
        # English Font
        ttk.Label(template_panel, text="English Font", style="Panel.TLabel").grid(row=7, column=0, sticky="w", pady=2)
        self.temp_font_en = ttk.Combobox(template_panel, values=["Arial", "Calibri", "Georgia", "Times New Roman"], state="normal", width=14)
        self.temp_font_en.grid(row=7, column=1, sticky="w", pady=2)
        
        # Font Sizes
        ttk.Label(template_panel, text="Ko Font Size", style="Panel.TLabel").grid(row=8, column=0, sticky="w", pady=2)
        self.temp_size_ko = tk.Spinbox(template_panel, from_=10, to=100, width=5, bg="#1e1e1e", fg="#ffffff", buttonbackground="#2d2d2d", insertbackground="#ffffff", bd=0)
        self.temp_size_ko.grid(row=8, column=1, sticky="w", pady=2)
        
        ttk.Label(template_panel, text="En Font Size", style="Panel.TLabel").grid(row=9, column=0, sticky="w", pady=2)
        self.temp_size_en = tk.Spinbox(template_panel, from_=10, to=100, width=5, bg="#1e1e1e", fg="#ffffff", buttonbackground="#2d2d2d", insertbackground="#ffffff", bd=0)
        self.temp_size_en.grid(row=9, column=1, sticky="w", pady=2)
        
        # Friendly Color Dropdowns
        ttk.Label(template_panel, text="Font Color", style="Panel.TLabel").grid(row=10, column=0, sticky="w", pady=2)
        self.temp_color = ttk.Combobox(template_panel, values=self.color_names, state="normal", width=14)
        self.temp_color.grid(row=10, column=1, sticky="w", pady=2)
        
        ttk.Label(template_panel, text="BG Color", style="Panel.TLabel").grid(row=11, column=0, sticky="w", pady=2)
        self.temp_bg = ttk.Combobox(template_panel, values=self.color_names, state="normal", width=14)
        self.temp_bg.grid(row=11, column=1, sticky="w", pady=2)
        
        # Checkbox Slide Splitting
        self.temp_split = ttk.Checkbutton(template_panel, text="One slide per verse")
        self.temp_split.grid(row=12, column=0, columnspan=2, sticky="w", pady=(8, 2))
        
        # ==================== BOTTOM ACTION PANEL ====================
        bottom_bar = ttk.Frame(self)
        bottom_bar.pack(fill="x", pady=(20, 10), padx=10)
        
        self.gen_btn = ttk.Button(bottom_bar, text="Generate PowerPoint Slide Deck", command=self._on_generate_ppt, width=30)
        self.gen_btn.pack(side="right")
        
        self.status_lbl = ttk.Label(bottom_bar, text="Status: Verifying input references...", foreground="#888888")
        self.status_lbl.pack(side="left")

    def _load_template_to_ui(self):
        """Populates UI controls from the self.template object."""
        # Bilingual mode mapping
        mode_reverse_map = {
            "ko_en": "Korean - English",
            "en_ko": "English - Korean",
            "ko_only": "Korean only",
            "en_only": "English only"
        }
        self.temp_mode.set(mode_reverse_map.get(self.template.bilingual_order, "Korean - English"))
        
        # Reference Order mapping
        ref_order_reverse_map = {
            "en_ko": "English - Korean",
            "ko_en": "Korean - English"
        }
        self.temp_ref_order.set(ref_order_reverse_map.get(self.template.ref_order, "Korean - English"))
        
        # Position / Alignment
        self.temp_v_loc.set(self.template.verse_location)
        self.temp_ref_loc.set(self.template.ref_location)
        self.temp_align.set(self.template.alignment)
        
        # Fonts
        self.temp_font_ko.set(self.template.font_ko)
        self.temp_font_en.set(self.template.font_en)
        
        # Font Sizes
        self.temp_size_ko.delete(0, "end")
        self.temp_size_ko.insert(0, str(self.template.font_size_ko))
        
        self.temp_size_en.delete(0, "end")
        self.temp_size_en.insert(0, str(self.template.font_size_en))
        
        # Colors
        hex_to_name = {v.upper(): k for k, v in self.color_map.items()}
        
        font_color_name = hex_to_name.get(self.template.font_color.upper(), self.template.font_color)
        self.temp_color.set(font_color_name)
        
        bg_color_name = hex_to_name.get(self.template.bg_color.upper(), self.template.bg_color)
        self.temp_bg.set(bg_color_name)
        
        # Checkbox
        self.temp_split.state(['selected'] if self.template.split_verses else ['!selected'])

    # ==================== RECURSIVE DROPDOWN CONTROLS ====================
    
    def _update_picker_chapters(self):
        book_name = self.pick_book.get()
        book = self.book_by_name[book_name]
        chapter_count = self.repo.get_chapter_count(book["id"])
        
        chapters = [str(i) for i in range(1, chapter_count + 1)]
        self.pick_chapter.configure(values=chapters)
        if chapters:
            self.pick_chapter.set("1")
            self._update_picker_verses()
        else:
            self.pick_chapter.set("")
            self.pick_start.configure(values=[])
            self.pick_start.set("")
            self.pick_end.configure(values=[])
            self.pick_end.set("")
            
    def _update_picker_verses(self):
        book_name = self.pick_book.get()
        book = self.book_by_name[book_name]
        ch = int(self.pick_chapter.get())
        verse_count = self.repo.get_verse_count(book["id"], ch)
        
        verses = [str(i) for i in range(1, verse_count + 1)]
        self.pick_start.configure(values=verses)
        self.pick_end.configure(values=verses)
        if verses:
            self.pick_start.set("1")
            self.pick_end.set("1")
        else:
            self.pick_start.set("")
            self.pick_end.set("")
            
    def _sync_picker_end_verse(self):
        start_v = int(self.pick_start.get())
        verses = list(self.pick_start.cget("values"))
        
        # End verse should be >= start verse
        valid_ends = [v for v in verses if int(v) >= start_v]
        self.pick_end.configure(values=valid_ends)
        if valid_ends:
            # If current selection is invalid, set to start verse
            curr_end = self.pick_end.get()
            if not curr_end or int(curr_end) < start_v:
                self.pick_end.set(str(start_v))

    def _add_picker_reference(self):
        book_name = self.pick_book.get()
        ch = self.pick_chapter.get()
        v_start = self.pick_start.get()
        v_end = self.pick_end.get()
        
        if not book_name or not ch or not v_start or not v_end:
            return
            
        ref_coord = f"{v_start}" if v_start == v_end else f"{v_start}-{v_end}"
        ref_string = f"{book_name} {ch}:{ref_coord}"
        
        # Insert into text box at current insert cursor
        cursor_pos = self.ref_text.index("insert")
        
        # Check if cursor is after non-empty text, insert semicolon
        line_content = self.ref_text.get("insert linestart", cursor_pos).strip()
        insert_text = ref_string
        if line_content and not line_content.endswith(";"):
            insert_text = "; " + ref_string
        else:
            insert_text = ref_string
            
        self.ref_text.insert(cursor_pos, insert_text)
        self.ref_text.focus_set()
        
        # Trigger validation
        self._trigger_async_validation()

    # ==================== ASYNCHRONOUS VERIFICATION ====================
    
    def _on_key_release(self, event):
        # Debounce key releases to prevent lagging during active typing
        if self.validation_timer:
            self.parent.after_cancel(self.validation_timer)
        self.validation_timer = self.parent.after(350, self._trigger_async_validation)
        
    def _trigger_async_validation(self):
        if self.validation_timer:
            self.parent.after_cancel(self.validation_timer)
            self.validation_timer = None
            
        text_content = self.ref_text.get("1.0", "end-1c")
        self.status_lbl.configure(text="Status: Verifying input references...", foreground="#888888")
        
        # Start parsing & database validation in a background thread to keep UI fluid
        threading.Thread(
            target=self._run_background_validation,
            args=(text_content,),
            daemon=True
        ).start()
        
    def _run_background_validation(self, text):
        parsed = Parser.parse_input_text(text)
        validated = []
        is_all_valid = True
        
        for entry in parsed:
            val_res = self.validator.validate_reference(entry)
            entry["valid"] = val_res["valid"]
            entry["description"] = val_res["description"]
            
            if not val_res["valid"]:
                is_all_valid = False
                
            validated.append(entry)
            
        # Put result in queue and alert main GUI thread
        self.validation_queue.put((is_all_valid, validated))

    def _poll_validation_queue(self):
        try:
            while True:
                is_all_valid, validated = self.validation_queue.get_nowait()
                self._update_ui_verification_results(is_all_valid, validated)
        except queue.Empty:
            pass
        finally:
            self.parent.after(100, self._poll_validation_queue)
            
    def _update_ui_verification_results(self, is_all_valid, validated):
        self.is_valid = is_all_valid
        self.parsed_entries = validated
        
        # 1. Clear previous text tags
        self.ref_text.tag_remove("valid_line", "1.0", "end")
        self.ref_text.tag_remove("invalid_line", "1.0", "end")
        
        # 2. Re-apply tags to lines and format logs
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        
        # Group descriptions by line number to format clean logs
        log_entries = []
        
        # Parse inputs by line to match tags precisely
        lines = self.ref_text.get("1.0", "end-1c").splitlines()
        
        # Map entries to line indexes
        entry_by_line = {}
        for entry in validated:
            line_no = entry["line_num"]
            if line_no not in entry_by_line:
                entry_by_line[line_no] = []
            entry_by_line[line_no].append(entry)
            
        for line_no, line_str in enumerate(lines, start=1):
            if not line_str.strip():
                continue
                
            line_entries = entry_by_line.get(line_no, [])
            line_all_valid = all(e["valid"] for e in line_entries) if line_entries else False
            
            # Select tag index
            tag = "valid_line" if line_all_valid else "invalid_line"
            self.ref_text.tag_add(tag, f"{line_no}.0", f"{line_no}.end")
            
            # Collate text descriptions
            for e in line_entries:
                bullet = "✓" if e["valid"] else "✗"
                color = "#a6e22e" if e["valid"] else "#f92672"
                
                # Write to the details text frame
                self.log_text.insert("end", f"[{line_no}] {bullet} {e['raw']} -> {e['description']}\n")
                
        self.log_text.configure(state="disabled")
        
        # 3. Update Generate Button and Status bar
        if not validated:
            self.is_valid = False
            self.status_lbl.configure(text="Status: Waiting for reference input...", foreground="#888888")
            self.gen_btn.configure(state="disabled")
        elif self.is_valid:
            self.status_lbl.configure(text="Status: All references verified successfully!", foreground="#a6e22e")
            self.gen_btn.configure(state="normal")
        else:
            self.status_lbl.configure(text="Status: Contains validation errors.", foreground="#f92672")
            self.gen_btn.configure(state="disabled")

    # ==================== PPT COMPILATION ====================
    
    def _read_ui_template(self) -> Template:
        """Reads values from UI controls and builds a complete Template object."""
        mode_map = {
            "Korean + English": "ko_en",
            "English + Korean": "en_ko",
            "Korean only": "ko_only",
            "English only": "en_only"
        }
        
        ref_order_map = {
            "English - Korean": "en_ko",
            "Korean - English": "ko_en"
        }
        
        self.template.bilingual_order = mode_map.get(self.temp_mode.get(), "ko_en")
        self.template.ref_order = ref_order_map.get(self.temp_ref_order.get(), "ko_en")
        self.template.verse_location = self.temp_v_loc.get()
        self.template.ref_location = self.temp_ref_loc.get()
        self.template.alignment = self.temp_align.get()
        self.template.font_ko = self.temp_font_ko.get()
        self.template.font_en = self.temp_font_en.get()
        
        try:
            self.template.font_size_ko = int(self.temp_size_ko.get())
        except ValueError:
            self.template.font_size_ko = 32
            
        try:
            self.template.font_size_en = int(self.temp_size_en.get())
        except ValueError:
            self.template.font_size_en = 32
            
        # Convert friendly color names to Hex strings
        font_color_ui = self.temp_color.get()
        self.template.font_color = self.color_map.get(font_color_ui, font_color_ui)
        
        bg_color_ui = self.temp_bg.get()
        self.template.bg_color = self.color_map.get(bg_color_ui, bg_color_ui)
        
        # Read checkbox state
        self.template.split_verses = "selected" in self.temp_split.state()
        
        return self.template

    def _on_generate_ppt(self):
        if not self.is_valid or not self.parsed_entries:
            messagebox.showerror("Error", "Cannot compile PPT with invalid or empty references.")
            return
            
        # Ask where to save PowerPoint file
        save_path = filedialog.asksaveasfilename(
            title="Save PowerPoint Slide Deck",
            defaultextension=".pptx",
            filetypes=[("PowerPoint Presentation", "*.pptx")]
        )
        
        if not save_path:
            return # User canceled
            
        if os.path.exists(save_path):
            confirm = messagebox.askyesno(
                "Confirm Overwrite",
                f"File '{os.path.basename(save_path)}' already exists.\nDo you want to overwrite it?"
            )
            if not confirm:
                return
                
        # Retrieve template settings
        template_settings = self._read_ui_template()
        
        # Compile PPT
        try:
            self.status_lbl.configure(text="Status: Generating PowerPoint file...", foreground="#888888")
            self.compiler.compile_ppt(
                parsed_refs=self.parsed_entries,
                template=template_settings,
                output_path=save_path,
                validator=self.validator
            )
            self.status_lbl.configure(text=f"Status: Saved to {os.path.basename(save_path)}!", foreground="#a6e22e")
            messagebox.showinfo("Success", f"PowerPoint file compiled successfully!\nSaved to: {save_path}")
        except Exception as e:
            self.status_lbl.configure(text="Status: PPT generation failed.", foreground="#f92672")
            messagebox.showerror("Execution Error", f"Failed to compile PowerPoint file:\n{e}")
            import traceback
            traceback.print_exc()
