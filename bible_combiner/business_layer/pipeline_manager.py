import os
from database_layer.books_metadata import BIBLE_BOOKS
from business_layer.mdb_extractor import MdbExtractor
from business_layer.alignment_engine import AlignmentEngine

class PipelineManager:
    def __init__(self, pool, mdb_repo, sqlite_repo, ui_handler=None):
        self.pool = pool
        self.mdb_repo = mdb_repo
        self.sqlite_repo = sqlite_repo
        self.ui = ui_handler
        self.extractor = MdbExtractor(self.mdb_repo)
        self.alignment_engine = AlignmentEngine()
        
    def run_pipeline(self, schema_sql_path: str):
        """Runs the complete ETL pipeline."""
        if self.ui:
            self.ui.show_info("Starting ETL Pipeline...")
            
        # 1. Verification
        if self.ui:
            self.ui.show_info("Verifying source files and ODBC drivers...")
        self.pool.verify_all_files_exist()
        
        # 2. Database Initialization
        if self.ui:
            self.ui.show_info("Initializing SQLite target database...")
        self.sqlite_repo.initialize_database(schema_sql_path)
        
        # 3. Populate Books Metadata
        if self.ui:
            self.ui.show_info("Populating Bible books metadata...")
        self.sqlite_repo.populate_books(BIBLE_BOOKS)
        
        # 4. Extract
        if self.ui:
            self.ui.show_info("Extracting verses from source databases...")
            
        if self.ui:
            self.ui.show_info("  Extracting Ngayok Version...")
        ngayok_verses = list(self.extractor.extract_verses("ngayok"))
        
        if self.ui:
            self.ui.show_info("  Extracting New International Version (NIV)...")
        niv_verses = list(self.extractor.extract_verses("niv"))
        
        # 5. Transform / Align
        if self.ui:
            self.ui.show_info("Aligning verses across all translations...")
        aligned_records, stats = self.alignment_engine.align(ngayok_verses, niv_verses)
        
        # 6. Load
        if self.ui:
            self.ui.show_info(f"Loading {len(aligned_records)} aligned records into SQLite...")
        self.sqlite_repo.insert_verses_batch(aligned_records)
        
        if self.ui:
            self.ui.show_success("Pipeline executed successfully!")
            self.ui.display_stats(stats)
            
        return stats
