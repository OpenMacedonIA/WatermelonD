from modules.database import DatabaseManager
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)

def init():
    print("Initializing Neo Brain Database...")
    try:
        db = DatabaseManager()
        # The __init__ method of DatabaseManager calls init_db(), which creates tables if they don't exist.
        # We can also explicitly check connection here.
        conn = db.get_connection()
        print("Database 'brain.db' created/verified successfully.")
        db.close()
    except Exception as e:
        print(f"Error initializing database: {e}")
        exit(1)

if __name__ == "__main__":
    init()
