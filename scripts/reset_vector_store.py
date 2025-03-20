import os
from pathlib import Path

def reset_vector_store():
    """Reset both the SQLite database and FAISS index"""
    # Define paths
    db_path = Path("vectors.db")
    faiss_path = Path("vectors.faiss")
    
    # Remove SQLite database if it exists
    if db_path.exists():
        try:
            os.remove(db_path)
            print(f"Removed SQLite database: {db_path}")
        except Exception as e:
            print(f"Error removing SQLite database: {e}")
    
    # Remove FAISS index if it exists
    if faiss_path.exists():
        try:
            os.remove(faiss_path)
            print(f"Removed FAISS index: {faiss_path}")
        except Exception as e:
            print(f"Error removing FAISS index: {e}")
    
    print("Vector store reset complete")

if __name__ == "__main__":
    # Ask for confirmation
    response = input("This will delete all vector store data. Are you sure? (y/N): ")
    if response.lower() == 'y':
        reset_vector_store()
    else:
        print("Reset cancelled")