import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go

# 1. PAGE SETUP
st.set_page_config(page_title="Gold Battery Master", layout="wide", page_icon="📀")

st.markdown("""
    <style>
    .revenue-box {
        background-color: #1a1a1a; border: 3px solid #FFD700; border-radius: 20px;
        padding: 40px; text-align: center; margin-bottom: 30px;
    }
    .revenue-text { color: #FFD700; font-size: 60px; font-weight: bold; }
    .revenue-label { color: #FFFFFF; font-size: 22px; }
    </style>
    """, unsafe_allow_html=True)

# 2. ENGINES (Market Data & Storage)
@st.cache_data(ttl=3600)
def get_market_master():
    try:
        gold = yf.Ticker("GC=F")
        hist = gold.history(period="2y") # Shows last 2 years for trend
        hist['INR_Rate'] = hist['Close'] * 88.5 * 0.3527 * 1.15
        return hist
    except:
        return pd.DataFrame()

def get_live_price():
    try:
        data = yf.Ticker("GC=F").history(period="1d")
        return round(data['Close'].iloc[-1] * 88.5 * 0.3527 * 1.15, 2)
    except:
        return 163800.0 # March 2026 fallback price

def load_data():
    try:
        df = pd.read_csv("gold_tracker.csv")
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except:
        return pd.DataFrame(columns=["Date", "Amount", "Entry_Rate", "Grams"])

# 3. INITIALIZE
df = load_data()
live_rate = get_live_price()
master_trend = get_market_master()

# 4. SIDEBAR CONTROLS
st.sidebar.header("🕹️ CONTROL PANEL")
use_auto = st.sidebar.checkbox("Auto-detect Date/Time", value=True)
entry_date = datetime.now() if use_auto else st.sidebar.date_input("Manual Date", datetime.now())
inv_amt = st.sidebar.number_input("Amount (₹)", min_value=0, value=80)

if st.sidebar.button("📀 LOG INVESTMENT"):
    net_amt = inv_amt * 0.97 # 3% GST
    grams_purchased = net_amt / (live_rate / 10)
    new_row = pd.DataFrame([{"Date": entry_date, "Amount": inv_amt, "Entry_Rate": live_rate, "Grams": grams_purchased}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv("gold_tracker.csv", index=False)
    st.rerun()

if not df.empty:
    st.sidebar.divider()
    st.sidebar.subheader("🗑️ CLEANUP")
    row_to_del = st.sidebar.selectbox("Select row to delete", df.index, format_func=lambda x: f"₹{df.loc[x, 'Amount']} on {df.loc[x, 'Date'].date()}")
    if st.sidebar.button("DELETE ENTRY"):
        df = df.drop(row_to_del)
        df.to_csv("gold_tracker.csv", index=False)
        st.rerun()

# 5. THE DASHBOARD
st.title("📀 Gold Battery & Master Trend")

if not df.empty:
    total_inv = df['Amount'].sum()
    total_grams = df['Grams'].sum()
    revenue = (total_grams * (live_rate / 10) * 0.97) - total_inv # 3% Sell Spread

    # BIG REVENUE BOX
    sym = "💰" if revenue >= 0 else "📉"
    st.markdown(f'<div class="revenue-box"><div class="revenue-label">TRADABLE TRADING REVENUE</div><div class="revenue-text">{sym} ₹{revenue:,.2f} {sym}</div></div>', unsafe_allow_html=True)

    # DUAL-LINE GRAPH
    if not master_trend.empty:
        st.subheader("📊 Global Market Trend vs. Your Entry")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=master_trend.index, y=master_trend['INR_Rate'], name="Market Trend", line=dict(color='rgba(150, 150, 150, 0.4)', width=1)))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Entry_Rate'], mode='markers+lines', name="Your Buys", line=dict(color='#FFD700', width=3), marker=dict(size=12, symbol='diamond', line=dict(width=2, color='white'))))
        fig.update_layout(template="plotly_dark", height=500, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    # METRICS
    m1, m2, m3 = st.columns(3)
    m1.metric("Live Price", f"₹{live_rate:,}/10g")
    m2.metric("Total Investment", f"₹{total_inv:,}")
    m3.metric("Gold Weight", f"{total_grams:.4f}g")
else:
    st.info("The battery is at 0%. Log your first entry in the sidebar to activate the Master Trend!")
