import os
import json
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from models import SessionLocal, Token, TokenMention, Message, TargetChannel, init_db
from parser import extract_ca, parse_rick_bot_response
from analysis import get_wallet_profile
from scoring import update_velocity, calculate_moonshot_score
from datetime import datetime

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')
RICK_BOT_ID = os.getenv('RICK_BOT_ID') or os.getenv('RICK_BOT')
if RICK_BOT_ID and str(RICK_BOT_ID).isdigit():
    RICK_BOT_ID = int(RICK_BOT_ID)

# Global list of channels to monitor
MONITORED_CHANNELS = []

# Fix DATABASE_URL if it has double @ due to password
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and "@@" in DATABASE_URL:
    # Assuming password@host format
    # Simple fix: replace the first @ in the user:pass@host part if we can identify it
    pass # Actually SQLAlchemy handles it better if we use %40 for the password @

async def refresh_channels(client, db):
    global MONITORED_CHANNELS
    while True:
        try:
            channels = db.query(TargetChannel).filter(TargetChannel.is_active == True).all()
            new_list = []
            for c in channels:
                val = c.identifier
                
                # Auto-resolve name if missing
                if not c.name:
                    try:
                        entity = await client.get_entity(int(val) if val.lstrip('-').isdigit() else val)
                        c.name = getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown'))
                        db.commit()
                        print(f"Resolved name for {val}: {c.name}")
                    except Exception as ex:
                        print(f"Could not resolve name for {val}: {ex}")

                if val.lstrip('-').isdigit():
                    new_list.append(int(val))
                else:
                    new_list.append(val)
            
            if set(new_list) != set(MONITORED_CHANNELS):
                print(f"Update detected. Now monitoring {len(new_list)} channels.")
                MONITORED_CHANNELS = new_list
        except Exception as e:
            print(f"Error refreshing channels: {e}")
        await asyncio.sleep(60)

async def main():
    # Initialize DB
    init_db()
    
    # Initialize Telethon Client
    client = TelegramClient('session_name', API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("Professional Memecoin Analyzer Worker is running...")

    db = SessionLocal()
    
    # Start background channel refresh
    asyncio.create_task(refresh_channels(client, db))

    @client.on(events.NewMessage())
    async def global_handler(event):
        # Only process if chat is in our monitored list
        chat_id = event.chat_id
        if chat_id not in MONITORED_CHANNELS and event.chat.username not in [str(c).replace('@', '') for c in MONITORED_CHANNELS if isinstance(c, str)]:
            # Special case for Rick Bot response
            if event.sender_id != RICK_BOT_ID:
                return

        text = event.message.message
        if not text: return

        # 1. Save to raw messages feed
        msg = Message(
            channel_id=str(chat_id),
            sender_id=str(event.sender_id),
            text=text
        )
        db.add(msg)
        db.commit()

        # 2. Case: Message from monitored channels
        if event.sender_id != RICK_BOT_ID:
            ca, platform = extract_ca(text)
            if ca:
                print(f"Detected CA: {ca} on {platform}. Sending to Rick Bot...")
                
                # Log the mention
                mention = TokenMention(contract_address=ca, source_channel=str(chat_id))
                db.add(mention)
                
                # Update Velocity and Initial Score
                token = db.query(Token).filter(Token.contract_address == ca).first()
                if not token:
                    token = Token(contract_address=ca, platform=platform)
                    db.add(token)
                
                m5, m15, m1h = update_velocity(ca, db)
                token.mentions_5m = m5
                token.mentions_15m = m15
                token.mentions_1h = m1h
                
                calculate_moonshot_score(token, db)
                db.commit()

                # Forward to Rick Bot
                try:
                    # Resolve entity first to ensure Telethon knows who it is
                    rick_entity = await client.get_entity(RICK_BOT_ID)
                    sent_msg = await client.send_message(rick_entity, ca)
                    print(f"Successfully forwarded CA to Rick Bot (Msg ID: {sent_msg.id})")
                except Exception as e:
                    print(f"❌ FAILED to send to Rick Bot: {e}")

        # 3. Case: Message from Rick Bot
        else:
            print("Received response from Rick Bot. Analyzing...")
            parsed_data = parse_rick_bot_response(text)
            
            if 'contract_address' in parsed_data:
                ca = parsed_data['contract_address']
                token = db.query(Token).filter(Token.contract_address == ca).first()
                if not token:
                    token = Token(contract_address=ca)
                    db.add(token)
                
                for key, value in parsed_data.items():
                    setattr(token, key, value)
                
                token.raw_response = text # Save the full raw text
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
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping worker gracefully...")
    except Exception as e:
        print(f"Unexpected error: {e}")
