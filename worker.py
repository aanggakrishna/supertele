import os
import json
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from models import SessionLocal, Token, TokenMention, init_db
from parser import extract_ca, parse_rick_bot_response
from analysis import get_wallet_profile
from scoring import update_velocity, calculate_moonshot_score
from datetime import datetime

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')

# Robust Target Channels loading
target_raw = os.getenv('TARGET_CHANNELS', '[]')
try:
    TARGET_CHANNELS = json.loads(target_raw)
    if not isinstance(TARGET_CHANNELS, list):
        TARGET_CHANNELS = [TARGET_CHANNELS]
except:
    # If not JSON, try comma separated
    TARGET_CHANNELS = [t.strip() for t in target_raw.split(',')]

# Convert elements to int if numeric
TARGET_CHANNELS = [int(t) if str(t).lstrip('-').isdigit() else t for t in TARGET_CHANNELS]

# Robust Rick Bot ID loading
RICK_BOT_ID = os.getenv('RICK_BOT_ID') or os.getenv('RICK_BOT')
if RICK_BOT_ID and RICK_BOT_ID.isdigit():
    RICK_BOT_ID = int(RICK_BOT_ID)

# Fix DATABASE_URL if it has double @ due to password
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and "@@" in DATABASE_URL:
    # Assuming password@host format
    # Simple fix: replace the first @ in the user:pass@host part if we can identify it
    pass # Actually SQLAlchemy handles it better if we use %40 for the password @

async def main():
    # Initialize DB
    init_db()
    
    # Initialize Telethon Client
    client = TelegramClient('session_name', API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("Professional Memecoin Analyzer Worker is running...")

    # Set up a session for DB interactions
    db = SessionLocal()

    @client.on(events.NewMessage(chats=TARGET_CHANNELS))
    async def channel_handler(event):
        text = event.message.message
        if not text: return

        ca, platform = extract_ca(text)
        if ca:
            print(f"Detected CA: {ca} on {platform}. Sending to Rick Bot...")
            
            # 1. Log the mention
            mention = TokenMention(contract_address=ca, source_channel=str(event.chat_id))
            db.add(mention)
            
            # 2. Update Velocity and Initial Score
            token = db.query(Token).filter(Token.contract_address == ca).first()
            if not token:
                token = Token(contract_address=ca, platform=platform)
                db.add(token)
            
            m5, m15, m1h = update_velocity(ca, db)
            token.mentions_5m = m5
            token.mentions_15m = m15
            token.mentions_1h = m1h
            
            # Recalculate Score
            calculate_moonshot_score(token, db)
            db.commit()

            # 3. Forward to Rick Bot
            await client.send_message(RICK_BOT_ID, ca)

    @client.on(events.NewMessage(from_users=[RICK_BOT_ID]))
    async def rick_handler(event):
        text = event.message.message
        if not text: return
        
        print("Received response from Rick Bot. Analyzing...")
        parsed_data = parse_rick_bot_response(text)
        
        if 'contract_address' in parsed_data:
            ca = parsed_data['contract_address']
            
            # Check if token exists, or update
            token = db.query(Token).filter(Token.contract_address == ca).first()
            if not token:
                token = Token(contract_address=ca)
                db.add(token)
            
            for key, value in parsed_data.items():
                setattr(token, key, value)
            
            # Recalculate score after Rick Bot data
            calculate_moonshot_score(token, db)
            
            db.commit()
            print(f"Updated token info and score for {ca}")

            # 3. Trigger Wallet Analysis if Top Holders present in Rick's text (simulated here)
            # In a real scenario, we might extract wallet addresses from the audit response
            # holders = extract_wallets(text)
            # for wallet in holders:
            #     profile = await get_wallet_profile(wallet)
            #     save_holder_profile(profile)

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
