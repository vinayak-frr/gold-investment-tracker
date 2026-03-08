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

# 2. ENGINES (Fixed for Current Indian Rates)
@st.cache_data(ttl=600)
def get_market_master():
    try:
        gold = yf.Ticker("GC=F")
        hist = gold.history(period="1y")
        # Fixed Multiplier: USD/oz * 0.3527 (to g) * 10 (to 10g) * Exch Rate (approx 83.5)
        # We removed the extra 1.15 premium that was causing the 185k error
        hist['INR_Rate'] = hist['Close'] * 0.3527 * 10 * 83.5 
        return hist
    except:
        return pd.DataFrame()

def get_live_price():
    try:
        data = yf.Ticker("GC=F").history(period="1d")
        return round(data['Close'].iloc[-1] * 0.3527 * 10 * 83.5, 2)
    except:
        return 163800.0 # Fallback safety for March 2026

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

# 4. SIDEBAR
st.sidebar.header("🕹️ CONTROL PANEL")
use_auto = st.sidebar.checkbox("Auto-detect Date/Time", value=True)
entry_date = datetime.now() if use_auto else st.sidebar.date_input("Pick Date", datetime.now())
inv_amt = st.sidebar.number_input("Amount (₹)", min_value=0, value=80)

if st.sidebar.button("📀 LOG INVESTMENT"):
    # CLEAN MATH: Raw Grams = Amount / (Price per 10g / 10)
    grams_purchased = inv_amt / (live_rate / 10)
    new_row = pd.DataFrame([{"Date": entry_date, "Amount": inv_amt, "Entry_Rate": live_rate, "Grams": grams_purchased}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv("gold_tracker.csv", index=False)
    st.rerun()

if not df.empty:
    st.sidebar.divider()
    if st.sidebar.button("🗑️ DELETE LAST ENTRY"):
        df = df[:-1]
        df.to_csv("gold_tracker.csv", index=False)
        st.rerun()

# 5. DASHBOARD
st.title("📀 Gold Battery Tracker (Pure Market)")

if not df.empty:
    total_inv = df['Amount'].sum()
    total_grams = df['Grams'].sum()
    # RAW REVENUE = (Grams * Current Price) - Total Invested
    revenue = (total_grams * (live_rate / 10)) - total_inv

    # THE BIG REVENUE BOX (No more forced negative start)
    sym = "💰" if revenue >= 0 else "📈"
    st.markdown(f"""
        <div class="revenue-box">
            <div class="revenue-label">PURE MARKET REVENUE</div>
            <div class="revenue-text">{sym} ₹{revenue:,.2f} {sym}</div>
        </div>
        """, unsafe_allow_html=True)

    # MASTER TREND GRAPH
    if not master_trend.empty:
        st.subheader("📊 Live Price vs. Your Entry")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=master_trend.index, y=master_trend['INR_Rate'], name="Market Trend", line=dict(color='rgba(255, 255, 255, 0.2)', width=1)))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Entry_Rate'], mode='markers+lines', name="Your Buys", line=dict(color='#FFD700', width=3), marker=dict(size=12, symbol='diamond')))
        fig.update_layout(template="plotly_dark", height=500, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    # METRICS
    m1, m2, m3 = st.columns(3)
    m1.metric("Live Market Price", f"₹{live_rate:,}")
    m2.metric("Total Investment", f"₹{total_inv:,}")
    m3.metric("Gold Weight", f"{total_grams:.4f}g")
else:
    st.info("Log your first entry. Current Live Price: ₹" + str(live_rate))
