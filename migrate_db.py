import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def migrate():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Migrating bot_schema.tokens table...")
        
        # List of columns to add
        columns = [
            ("mentions_5m", "INTEGER DEFAULT 0"),
            ("mentions_15m", "INTEGER DEFAULT 0"),
            ("mentions_1h", "INTEGER DEFAULT 0"),
            ("velocity_score", "NUMERIC DEFAULT 0"),
            ("moonshot_score", "NUMERIC DEFAULT 0"),
            ("is_gold", "BOOLEAN DEFAULT FALSE"),
            ("trader_notes", "TEXT")
        ]
        
        for col_name, col_type in columns:
            try:
                cur.execute(f"ALTER TABLE bot_schema.tokens ADD COLUMN {col_name} {col_type};")
                print(f"Added column: {col_name}")
            except psycopg2.errors.DuplicateColumn:
                print(f"Column {col_name} already exists, skipping.")
                continue

        print("Migration completed successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
