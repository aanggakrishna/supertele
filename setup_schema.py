import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def setup_schema():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Attempting to create 'bot_schema'...")
        cur.execute("CREATE SCHEMA IF NOT EXISTS bot_schema AUTHORIZATION bot_user;")
        print("Schema 'bot_schema' created or already exists.")
        
        # Set search path
        cur.execute("ALTER USER bot_user SET search_path TO bot_schema, public;")
        print("Search path updated for bot_user.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_schema()
