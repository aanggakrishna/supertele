import os
import json
from dotenv import load_dotenv
from telethon import TelegramClient, events
import psycopg2
from psycopg2 import sql

# Load environment variables
load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')
DATABASE_URL = os.getenv('DATABASE_URL')
TARGET_CHANNELS = json.loads(os.getenv('TARGET_CHANNELS', '[]'))

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            channel_id TEXT,
            sender_id TEXT,
            message_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id SERIAL PRIMARY KEY,
            token_symbol TEXT,
            contract_address TEXT,
            mentions INTEGER DEFAULT 1,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def save_message(channel_id, sender_id, text):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO messages (channel_id, sender_id, message_text) VALUES (%s, %s, %s)',
            (str(channel_id), str(sender_id), text)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error saving message: {e}")

async def main():
    # Initialize DB
    init_db()
    
    # Initialize Telethon Client
    client = TelegramClient('session_name', API_ID, API_HASH)
    
    await client.start(phone=PHONE)
    print("Client is running...")

    @client.on(events.NewMessage(chats=TARGET_CHANNELS))
    async def handler(event):
        sender = await event.get_sender()
        sender_id = sender.id if sender else "Unknown"
        text = event.message.message
        channel_id = event.chat_id
        
        print(f"New message from {channel_id} ({sender_id}): {text[:50]}...")
        save_message(channel_id, sender_id, text)
        # TODO: Add analysis logic here

    await client.run_until_disconnected()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
