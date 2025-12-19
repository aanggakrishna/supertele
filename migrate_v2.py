import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def migrate_v2():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Creating new tables in bot_schema...")
        
        # Create messages table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bot_schema.messages (
                id SERIAL PRIMARY KEY,
                channel_id TEXT,
                sender_id TEXT,
                text TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create target_channels table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bot_schema.target_channels (
                id SERIAL PRIMARY KEY,
                identifier TEXT UNIQUE,
                name TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        print("Migration v2 completed successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error during migration v2: {e}")

if __name__ == "__main__":
    migrate_v2()
