import sys
from pathlib import Path
from src.ingestor import ingest_all_mhtml
# from src.processor import process_all_html 
# from src.loader import load_all_jsons      
# from src.profiler import run_data_profile   

SOURCE_DIR = Path("data/0_source")
BRONZE_DIR = Path("data/1_bronze")
# SILVER_DIR = Path("data/2_silver")
# GOLD_DIR = Path("data/3_gold")
DB_NAME = "jobs.db"

def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python main.py [ingest|process|load|profile|full]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Route to appropriate function
    if command == "ingest":
        ingest_all_mhtml(str(SOURCE_DIR), str(BRONZE_DIR))
    elif command == "process":
        # process_all_html(str(BRONZE_DIR), str(SILVER_DIR))
        print("Process command - to be implemented")
    elif command == "load":
        # load_all_jsons(str(SILVER_DIR), str(GOLD_DIR))
        print("Load command - to be implemented")
    elif command == "profile":
        # run_data_profile(str(GOLD_DIR / DB_NAME))
        print("Profile command - to be implemented")
    elif command == "full":
        print("Full pipeline - to be implemented")
    else:
        print(f"Unknown command: {command}")
        print("Available: ingest, process, load, profile, full")
        sys.exit(1)

if __name__ == "__main__":
    main()