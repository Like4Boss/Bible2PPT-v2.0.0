import colorama
from colorama import Fore, Style
from database_layer.books_metadata import BIBLE_BOOKS

class TerminalUI:
    def __init__(self):
        # Initialize colorama, resolving Windows ANSI support automatically
        colorama.init(autoreset=True)
        
        # Build quick book mapping for display
        self.book_names = {b["id"]: b["ko"] for b in BIBLE_BOOKS}
        
    def show_info(self, message: str):
        print(f"{Fore.CYAN}[INFO] {Style.RESET_ALL}{message}")
        
    def show_success(self, message: str):
        print(f"{Fore.GREEN}[SUCCESS] {Style.RESET_ALL}{message}")
        
    def show_warning(self, message: str):
        print(f"{Fore.YELLOW}[WARNING] {Style.RESET_ALL}{message}")
        
    def show_error(self, message: str):
        print(f"{Fore.RED}[ERROR] {Style.RESET_ALL}{message}")
        
    def _format_coord(self, book_id: int, chapter: int, verse: int) -> str:
        book_name = self.book_names.get(book_id, f"Book {book_id}")
        return f"{book_name} {chapter}:{verse}"
        
    def display_stats(self, stats: dict):
        print(f"\n{Fore.MAGENTA}=== ETL Execution Statistics ==={Style.RESET_ALL}")
        print(f"Total Unique Aligned Verses: {Fore.WHITE}{Style.BRIGHT}{stats['total_unique_verses']}{Style.RESET_ALL}")
        
        for key in ["ngayok", "niv"]:
            info = stats[key]
            name = key.upper()
            count = info["count"]
            omitted = info["omitted_count"]
            
            print(f"\n{Fore.BLUE}{Style.BRIGHT}{name} Version:{Style.RESET_ALL}")
            print(f"  Mapped Verses: {Fore.GREEN}{count}{Style.RESET_ALL}")
            if omitted > 0:
                print(f"  Omitted Verses: {Fore.RED}{omitted}{Style.RESET_ALL}")
                print(f"  Omitted List (truncated to first 10):")
                for coord in info["omitted_details"][:10]:
                    print(f"    - {self._format_coord(*coord)}")
                if omitted > 10:
                    print(f"    - ... and {omitted - 10} more.")
            else:
                print(f"  Omitted Verses: {Fore.GREEN}0 (Full text coverage){Style.RESET_ALL}")
                
        print(f"\n{Fore.MAGENTA}================================{Style.RESET_ALL}\n")
