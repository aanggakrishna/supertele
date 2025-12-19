import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def migrate_v3():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Adding raw_response column to bot_schema.tokens...")
        try:
            cur.execute("ALTER TABLE bot_schema.tokens ADD COLUMN raw_response TEXT;")
            print("Added column: raw_response")
        except psycopg2.errors.DuplicateColumn:
            print("Column raw_response already exists.")

        print("Migration v3 completed successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error during migration v3: {e}")

if __name__ == "__main__":
    migrate_v3()
