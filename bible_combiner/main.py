import os
import sys
import argparse

# Ensure bible-combiner directory is in the python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_layer.connection_pool import ConnectionPool
from persistence_layer.mdb_repository import MdbRepository
from persistence_layer.sqlite_repository import SqliteRepository
from business_layer.pipeline_manager import PipelineManager
from ui_layer.terminal_ui import TerminalUI

def main():
    # Reconfigure stdout to UTF-8 to prevent encoding crashes on Windows with non-ASCII text
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # sys.stdout might not support reconfiguration in some test environments
        
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Configure argument parsing
    parser = argparse.ArgumentParser(description="Combine legacy Access databases into a unified SQLite database.")
    parser.add_argument(
        "--mdb-dir",
        default=os.path.abspath(os.path.join(script_dir, "..", "bible_data")),
        help="Path to directory containing ngayok.mdb and nivdb.mdb"
    )
    parser.add_argument(
        "--sqlite-path",
        default=os.path.abspath(os.path.join(script_dir, "unified_bible.db")),
        help="Path where output unified SQLite database should be created"
    )
    args = parser.parse_args()
    
    ui = TerminalUI()
    
    schema_sql_path = os.path.join(script_dir, "database_layer", "unified_schema.sql")
    
    try:
        # Initialize connection pool
        pool = ConnectionPool(mdb_dir=args.mdb_dir, sqlite_path=args.sqlite_path)
        
        # Initialize repositories
        mdb_repo = MdbRepository(pool)
        sqlite_repo = SqliteRepository(pool)
        
        # Initialize and run pipeline
        manager = PipelineManager(
            pool=pool,
            mdb_repo=mdb_repo,
            sqlite_repo=sqlite_repo,
            ui_handler=ui
        )
        
        manager.run_pipeline(schema_sql_path)
        
    except Exception as e:
        ui.show_error(f"Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
