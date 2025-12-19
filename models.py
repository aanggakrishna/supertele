import os
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Token(Base):
    __tablename__ = 'tokens'
    __table_args__ = {'schema': 'bot_schema'}
    id = Column(Integer, primary_key=True, index=True)
    contract_address = Column(String, unique=True, index=True)
    symbol = Column(String)
    name = Column(String)
    platform = Column(String)
    fdv = Column(Numeric)
    liquidity = Column(Numeric)
    volume_24h = Column(Numeric)
    top_holders_percent = Column(Numeric)
    rick_score = Column(Integer)
    audit_status = Column(String)
    pump_prob = Column(Numeric)
    best_entry_time = Column(DateTime)
    
    # Moonshot Metrics
    mentions_5m = Column(Integer, default=0)
    mentions_15m = Column(Integer, default=0)
    mentions_1h = Column(Integer, default=0)
    velocity_score = Column(Numeric, default=0) # Rate of mentions growth
    
    moonshot_score = Column(Numeric, default=0) # 0-100 score
    is_gold = Column(Boolean, default=False)
    
    trader_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class HolderAnalysis(Base):
    __tablename__ = 'holders_analysis'
    __table_args__ = {'schema': 'bot_schema'}
    wallet_address = Column(String, primary_key=True)
    wallet_age_days = Column(Integer)
    total_volume_sol = Column(Numeric)
    trading_style = Column(String) # 'Diamond Hand', 'Swing', 'Bot', 'Rugger'
    win_rate = Column(Numeric)
    last_updated = Column(DateTime, default=datetime.utcnow)

class TokenMention(Base):
    __tablename__ = 'token_mentions'
    __table_args__ = {'schema': 'bot_schema'}
    id = Column(Integer, primary_key=True)
    contract_address = Column(String, index=True)
    source_channel = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
