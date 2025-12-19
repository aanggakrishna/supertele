import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def check_perms():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check current user
        cur.execute("SELECT current_user, current_database();")
        user, db = cur.fetchone()
        print(f"Logged in as: {user} on database: {db}")
        
        # Check schema permissions
        cur.execute("""
            SELECT has_schema_privilege('bot_user', 'public', 'CREATE'),
                   has_schema_privilege('bot_user', 'public', 'USAGE');
        """)
        can_create, can_use = cur.fetchone()
        print(f"Can create in public: {can_create}")
        print(f"Can use public: {can_use}")
        
        # Try a dummy create
        print("Attempting to create a test table...")
        cur.execute("CREATE TABLE IF NOT EXISTS test_connection (id serial);")
        conn.commit()
        print("Success! Test table created.")
        
        cur.execute("DROP TABLE test_connection;")
        conn.commit()
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_perms()
