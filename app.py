import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import plotly.express as px

# 1. PAGE CONFIG
st.set_page_config(page_title="Gold Battery Tracker", layout="wide", page_icon="📀")

# Custom Styling for the Big Revenue Box
st.markdown("""
    <style>
    .revenue-box {
        background-color: #1a1a1a;
        border: 3px solid #FFD700;
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0px 0px 20px rgba(255, 215, 0, 0.2);
    }
    .revenue-text {
        color: #FFD700;
        font-size: 60px;
        font-weight: bold;
    }
    .revenue-label {
        color: #FFFFFF;
        font-size: 22px;
        letter-spacing: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA LOAD
def load_data():
    try:
        return pd.read_csv("gold_tracker.csv", parse_dates=["Date"])
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "Amount", "Entry_Rate", "Grams"])

# 3. LIVE MARKET DATA (Adjusted for 2026 Indian 24k Gold)
def get_live_rate():
    try:
        gold = yf.Ticker("GC=F")
        data = gold.history(period="1d")
        current_usd = data['Close'].iloc[-1]
        # 2026 conversion: USD to INR * grams per oz * import duty/premium factor
        return round(current_usd * 88.5 * 0.3527 * 1.15, 2)
    except:
        return 163800.0 # Fallback safety rate

# 4. LOGIC ENGINE
df = load_data()
live_rate_10g = get_live_rate()

# SIDEBAR: ENTRY SYSTEM
st.sidebar.header("📥 LOG INVESTMENT")
use_auto = st.sidebar.checkbox("Auto-detect Date & Time", value=True)
if use_auto:
    entry_date = datetime.now()
else:
    entry_date = st.sidebar.date_input("Manual Date Selection", datetime.now())

inv_amount = st.sidebar.number_input("Amount (₹)", min_value=0, value=80)

if st.sidebar.button("ADD TO BATTERY"):
    # Subtract 3% GST immediately to get 'Net Investment'
    net_val = inv_amount * 0.97
    grams = net_val / (live_rate_10g / 10)
    
    new_entry = pd.DataFrame([{"Date": entry_date, "Amount": inv_amount, "Entry_Rate": live_rate_10g, "Grams": grams}])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv("gold_tracker.csv", index=False)
    st.sidebar.success("Logged to Gold Battery! 📀")
    st.rerun()

# 5. DASHBOARD VISUALS
st.title("📀 Gold Battery: Phase 1 Dashboard")

if not df.empty:
    total_invested = df['Amount'].sum()
    total_grams = df['Grams'].sum()
    
    # REAL-TIME CALCULATION
    # What it's worth now (applying 3% sell spread because Jar doesn't sell at market buy price)
    current_cash_value = (total_grams * (live_rate_10g / 10)) * 0.97
    revenue = current_cash_value - total_invested

    # THE BIG REVENUE BOX (Requirement #5)
    sym = "💰💵💰" if revenue >= 0 else "📉💸📉"
    st.markdown(f"""
        <div class="revenue-box">
            <div class="revenue-label">TRADABLE REVENUE (PHASE 2 AMMO)</div>
            <div class="revenue-text">{sym} ₹{revenue:,.2f} {sym}</div>
        </div>
    """, unsafe_allow_html=True)

    # Secondary Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Live Market Rate", f"₹{live_rate_10g:,}/10g")
    m2.metric("Total Invested", f"₹{total_invested:,}")
    m3.metric("Grams Accumulated", f"{total_grams:.4f}g")

    # The Visual Graph (Requirement #2)
    st.subheader("📈 Entry Rate History")
    fig = px.area(df, x="Date", y="Entry_Rate", title="Market Price at each Buy", color_discrete_sequence=['gold'])
    st.plotly_chart(fig, use_container_width=True)

    # History Table (Requirement #4)
    st.subheader("📅 Investment Log")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
else:
    st.info("Battery is empty. Start logging to see your growth.")
