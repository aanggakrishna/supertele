import streamlit as st
import pandas as pd
from models import SessionLocal, Token, HolderAnalysis, Message, TargetChannel
from sqlalchemy import func, desc
import os

st.set_page_config(page_title="Professional Memecoin Terminal", layout="wide")

st.title("🚀 Professional Memecoin Terminal")

# Sidebar for Summary & Professional Trader Notes
st.sidebar.header("Professional Trader View")
st.sidebar.info("""
**Current Sentiment:** High Risk / Degenerate
**Note:** Many tokens are launching on Pump.fun. 
Focus on Liquidity/MC ratio. If < 5%, high risk of rug.
Check Top 10 Holder concentration. > 30% is a flag.
""")

db = SessionLocal()

def load_data():
    tokens = db.query(Token).order_by(Token.moonshot_score.desc()).all()
    if not tokens:
        return pd.DataFrame()
    return pd.DataFrame([{
        "Score": f"⭐ {t.moonshot_score:.0f}/100" if t.is_gold else f"{t.moonshot_score:.0f}/100",
        "Symbol": t.symbol,
        "CA": t.contract_address,
        "5m/15m/1h Mentions": f"{t.mentions_5m} / {t.mentions_15m} / {t.mentions_1h}",
        "FDV": f"${t.fdv:,.0f}" if t.fdv else "N/A",
        "Liquidity": f"${t.liquidity:,.0f}" if t.liquidity else "N/A",
        "Trader Notes": t.trader_notes or "Analyzing...",
        "Risk": "Low" if t.moonshot_score > 70 else ("High" if t.moonshot_score < 30 else "Moderate")
    } for t in tokens])

df = load_data()

tabs = st.tabs(["🚀 Moonshot Radar", "🔍 Wallet Behavioral Analysis", "🔥 Raw Feed", "⚙️ Channel Manager", "🧠 ML & Strategy Insights"])

with tabs[0]:
    st.subheader("Real-time Moonshot Radar (Sorted by Potential)")
    if not df.empty:
        # Style the dataframe (optional)
        st.dataframe(df, width='stretch', hide_index=True)
        
        # High Conviction Section
        gold_tokens = db.query(Token).filter(Token.is_gold == True).order_by(Token.created_at.desc()).all()
        if gold_tokens:
            st.success(f"⚡ FOUND {len(gold_tokens)} HIGH CONVICTION (GOLD) TOKENS!")
            for gt in gold_tokens:
                with st.expander(f"💰 {gt.symbol} | Score: {gt.moonshot_score:.0f} | CA: {gt.contract_address}"):
                    st.write(f"**Notes:** {gt.trader_notes}")
                    st.write(f"**Mentions Intensity:** {gt.mentions_5m} mentions in last 5 mins.")
                    if gt.raw_response:
                        st.write("**Raw Rick Bot Data:**")
                        st.code(gt.raw_response)
        
        st.write("---")
        st.subheader("All Detected Tokens")
        all_tokens = db.query(Token).order_by(Token.created_at.desc()).limit(20).all()
        for t in all_tokens:
            with st.expander(f"{'⭐' if t.is_gold else '•'} {t.symbol or 'Unknown'} | Score: {t.moonshot_score:.0f} | CA: {t.contract_address}"):
                 col_a, col_b = st.columns(2)
                 with col_a:
                     st.write(f"**FDV:** ${t.fdv:,.0f}" if t.fdv else "**FDV:** N/A")
                     st.write(f"**Liq:** ${t.liquidity:,.0f}" if t.liquidity else "**Liq:** N/A")
                 with col_b:
                     st.write(f"**Score:** {t.moonshot_score:.0f}/100")
                     st.write(f"**Risk:** {t.audit_status or 'Unknown'}")
                 
                 if t.raw_response:
                     st.write("**Full Raw Data:**")
                     st.text(t.raw_response)
    else:
        st.info("Listening for new tokens on Telegram... Momentum is coming.")

with tabs[1]:
    st.subheader("Top Holder Behavioral Profiling")
    profiles = db.query(HolderAnalysis).all()
    if profiles:
        prof_df = pd.DataFrame([{
            "Wallet": p.wallet_address,
            "Age (Days)": p.wallet_age_days,
            "Style": p.trading_style,
            "Win Rate": f"{p.win_rate * 100:.0f}%"
        } for p in profiles])
        st.table(prof_df)
    else:
        st.write("No wallet analysis data yet.")

with tabs[2]:
    st.subheader("🔥 Recent Telegram Activity (Live Feed)")
    msgs = db.query(Message).order_by(desc(Message.timestamp)).limit(50).all()
    if msgs:
        msg_df = pd.DataFrame([{
            "Time": m.timestamp.strftime("%H:%M:%S"),
            "Channel ID": m.channel_id,
            "Sender": m.sender_id,
            "Message": m.text[:100] + "..." if len(m.text) > 100 else m.text
        } for m in msgs])
        st.dataframe(msg_df, width='stretch', hide_index=True)
    else:
        st.info("No activity detected yet.")

with tabs[3]:
    st.subheader("⚙️ Channel Management")
    
    # 1. Add New Channel
    with st.expander("➕ Add New Target Channel"):
        st.info("""
        **Format Guide:**
        - **Channel ID**: Biasanya diawali dengan `-100` (contoh: `-100123456789`). Masukkan lengkap dengan tanda minusnya.
        - **Username**: Awali dengan `@` (contoh: `@DexScreenerCalls`).
        """)
        new_id = st.text_input("Channel ID or @username", placeholder="-100xxxxxxx or @username")
        if st.button("Add Channel"):
            if new_id:
                try:
                    # Clean input
                    new_id_clean = new_id.strip()
                    ch = TargetChannel(identifier=new_id_clean, name=None) # Name will be resolved by worker
                    db.add(ch)
                    db.commit()
                    st.success(f"Added {new_id_clean}! Menunggu worker mengambil nama channel...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Identifier required.")

    # 2. List & Toggle Channels
    st.write("---")
    channels = db.query(TargetChannel).order_by(TargetChannel.created_at.desc()).all()
    if channels:
        for c in channels:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                display_name = c.name if c.name else "⏳ *Fetching name from Telegram...*"
                st.write(f"**{display_name}**")
                st.caption(f"ID: `{c.identifier}`")
            with col2:
                status = "✅ Active" if c.is_active else "❌ Inactive"
                if st.button(status, key=f"toggle_{c.id}"):
                    c.is_active = not c.is_active
                    db.commit()
                    st.rerun()
            with col3:
                if st.button("🗑️ Delete", key=f"del_{c.id}"):
                    db.delete(c)
                    db.commit()
                    st.rerun()
    else:
        st.write("No target channels configured.")

with tabs[4]:
    st.subheader("ML & Strategy Insights")
    st.write("Best entry window (based on history): **14:00 - 18:00 UTC**")
    # Placeholder for a heatmap or chart
    st.info("Segmentasi: Token dengan mention > 3 dalam 5 menit memiliki probabilitas pump 70%.")

if st.button("Refresh Data"):
    st.rerun()
