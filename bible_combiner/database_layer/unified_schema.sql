-- Schema definition for the Unified Bible SQLite Database

CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY,
    name_ko TEXT NOT NULL UNIQUE,
    name_en TEXT NOT NULL,
    abbr_en TEXT NOT NULL,
    abbr_ko TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS verses (
    book_id INTEGER NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    ngayok TEXT,
    niv TEXT,
    PRIMARY KEY (book_id, chapter, verse),
    FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
);

-- Index for fast searches by book and chapter
CREATE INDEX IF NOT EXISTS idx_verses_lookup ON verses(book_id, chapter);
