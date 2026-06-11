import os
import sys
import tkinter as tk

# Add project root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import Database
from core.repository import Repository
from gui.interface import Interface

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.abspath(os.path.join(script_dir, "..", "bible_combiner", "unified_bible.db"))
            
    # Initialize layers
    try:
        db = Database(db_path)
        repo = Repository(db)
    except Exception as e:
        print(f"Error initializing database layer: {e}")
        sys.exit(1)
        
    # Setup Main Tkinter Window
    root = tk.Tk()
    root.title("Bible2PPT - Slide Compilation Tool")
    root.geometry("1024x720")
    root.minsize(960, 680)
    
    # Initialize UI presentation layer
    app = Interface(parent=root, repository=repo)
    app.pack(fill="both", expand=True)
    
    # Run the window loop
    root.mainloop()

if __name__ == "__main__":
    main()
