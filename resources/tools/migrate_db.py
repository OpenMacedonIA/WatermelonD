import sqlite3
import os

DB_PATH = "brain/brain.db"

def migrate_db():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if context_json exists
    try:
        cursor.execute("SELECT context_json FROM episodic_memory LIMIT 1")
        print("Column 'context_json' already exists.")
    except sqlite3.OperationalError:
        print("Adding 'context_json' column...")
        try:
            cursor.execute("ALTER TABLE episodic_memory ADD COLUMN context_json TEXT DEFAULT '{}'")
            conn.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")
            
    conn.close()

if __name__ == "__main__":
    migrate_db()
