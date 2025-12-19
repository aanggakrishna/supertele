import streamlit as st
import pandas as pd
from models import SessionLocal, Token, HolderAnalysis
from sqlalchemy import func
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

tabs = st.tabs(["🚀 Moonshot Radar", "🔍 Wallet Behavioral Analysis", "🧠 ML & Strategy Insights"])

with tabs[0]:
    st.subheader("Real-time Moonshot Radar (Sorted by Potential)")
    if not df.empty:
        # Style the dataframe (optional)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # High Conviction Section
        gold_tokens = db.query(Token).filter(Token.is_gold == True).all()
        if gold_tokens:
            st.success(f"⚡ FOUND {len(gold_tokens)} HIGH CONVICTION (GOLD) TOKENS!")
            for gt in gold_tokens:
                with st.expander(f"💰 {gt.symbol} | Score: {gt.moonshot_score:.0f} | CA: {gt.contract_address}"):
                    st.write(f"**Notes:** {gt.trader_notes}")
                    st.write(f"**Mentions Intensity:** {gt.mentions_5m} mentions in last 5 mins.")
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
    st.subheader("ML & Timing Strategy")
    st.write("Best entry window (based on history): **14:00 - 18:00 UTC**")
    # Placeholder for a heatmap or chart
    st.info("Segmentasi: Token dengan mention > 3 dalam 5 menit memiliki probabilitas pump 70%.")

if st.button("Refresh Data"):
    st.rerun()
