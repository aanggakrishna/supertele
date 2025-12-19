from datetime import datetime, timedelta
from models import Token, TokenMention, SessionLocal
from sqlalchemy import func

def calculate_moonshot_score(token: Token, db):
    """
    Algorithm to score tokens based on momentum, liquidity, and audit.
    Score range: 0 - 100
    """
    score = 0
    notes = []

    # 1. Mention Velocity (Max 40 points)
    # Higher velocity in short timeframes = higher score
    if token.mentions_5m >= 3:
        score += 30
        notes.append("🔥 High Social Velocity (5m)")
    elif token.mentions_15m >= 5:
        score += 20
        notes.append("📈 Growing Interest (15m)")
    
    # 2. Liquidity & FDV Ratio (Max 30 points)
    if token.liquidity and token.fdv:
        liq_to_mc = (float(token.liquidity) / float(token.fdv)) * 100
        if 5 <= liq_to_mc <= 25:
            score += 20
            notes.append("✅ Healthy Liquidity/MC ratio")
        elif liq_to_mc < 2:
            score -= 10
            notes.append("⚠️ Extremely Low Liquidity (High Risk)")
    
    # 3. Rick Bot Audit (Max 30 points)
    if token.risk_score:
        # Assuming lower is better for risk_score from Rick
        audit_val = max(0, 30 - token.risk_score)
        score += audit_val
        if token.risk_score < 5:
            notes.append("🛡️ Clean Audit from Rick Bot")
    
    # 4. Holder Saturation
    if token.top_holders_percent:
        if token.top_holders_percent > 40:
            score -= 20
            notes.append("🚨 Top Holders > 40% (Potential Rug)")
        elif token.top_holders_percent < 15:
            score += 10
            notes.append("💎 Great Holder Distribution")

    token.moonshot_score = min(100, max(0, score))
    token.is_gold = token.moonshot_score >= 80
    token.trader_notes = " | ".join(notes)
    
    return token

def update_velocity(ca: str, db):
    """
    Recalculates mention counts for different timeframes
    """
    now = datetime.utcnow()
    
    m5 = db.query(TokenMention).filter(
        TokenMention.contract_address == ca,
        TokenMention.timestamp >= now - timedelta(minutes=5)
    ).count()
    
    m15 = db.query(TokenMention).filter(
        TokenMention.contract_address == ca,
        TokenMention.timestamp >= now - timedelta(minutes=15)
    ).count()
    
    m1h = db.query(TokenMention).filter(
        TokenMention.contract_address == ca,
        TokenMention.timestamp >= now - timedelta(hours=1)
    ).count()
    
    return m5, m15, m1h
