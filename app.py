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

# 2. THE ERROR-PROOF MARKET ENGINE
@st.cache_data(ttl=600)
def get_clean_data():
    gold = yf.Ticker("GC=F")
    # Get 1 year of history
    hist = gold.history(period="1y")
    
    # Fix the 1.5 million bug: If price > 10,000, it's in cents. Divide by 100.
    hist['Close'] = hist['Close'].apply(lambda x: x/100 if x > 10000 else x)
    
    # Conversion: USD * 0.3527 * 10 * 83.5 (Strict conversion)
    hist['INR_Rate'] = hist['Close'] * 0.3527 * 10 * 83.5
    return hist

df_market = get_clean_data()
live_rate = round(df_market['INR_Rate'].iloc[-1], 2)

# 3. DATA LOAD
def load_data():
    try:
        df = pd.read_csv("gold_tracker.csv")
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except:
        return pd.DataFrame(columns=["Date", "Amount", "Entry_Rate", "Grams"])

df_user = load_data()

# 4. SIDEBAR
st.sidebar.header("🕹️ CONTROL")
amt = st.sidebar.number_input("Amount (₹)", min_value=0, value=263)
if st.sidebar.button("📀 LOG"):
    # Rounding to 6 decimal places to kill the "magic debt"
    grams = round(amt / (live_rate / 10), 6)
    new_row = pd.DataFrame([{"Date": datetime.now(), "Amount": amt, "Entry_Rate": live_rate, "Grams": grams}])
    df_user = pd.concat([df_user, new_row], ignore_index=True)
    df_user.to_csv("gold_tracker.csv", index=False)
    st.rerun()

if not df_user.empty and st.sidebar.button("🗑️ DELETE LAST"):
    df_user = df_user[:-1]
    df_user.to_csv("gold_tracker.csv", index=False)
    st.rerun()

# 5. DASHBOARD
st.title("📀 Gold Battery Tracker")

if not df_user.empty:
    total_inv = round(df_user['Amount'].sum(), 2)
    total_grams = round(df_user['Grams'].sum(), 6)
    # Current Value = Total Grams * (Current Price / 10)
    current_val = round(total_grams * (live_rate / 10), 2)
    revenue = round(current_val - total_inv, 2)

    # REVENUE BOX
    sym = "💰" if revenue >= -0.01 else "📈"
    # Added a small buffer (>= -0.01) so 0.00 doesn't show as a loss due to tiny math errors
    st.markdown(f"""
        <div class="revenue-box">
            <div class="revenue-label">NET MARKET REVENUE</div>
            <div class="revenue-text">{sym} ₹{revenue:,.2f} {sym}</div>
        </div>
        """, unsafe_allow_html=True)

    # THE GRAPH (Fixed with proper Market Data)
    st.subheader("📊 Gold Trend & Your Entries")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_market.index, y=df_market['INR_Rate'], name="Market", line=dict(color='grey', width=1)))
    fig.add_trace(go.Scatter(x=df_user['Date'], y=df_user['Entry_Rate'], mode='markers+lines', name="Your Buys", line=dict(color='gold', width=3), marker=dict(size=12, symbol='diamond')))
    fig.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig, use_container_width=True)

    # STATS
    c1, c2, c3 = st.columns(3)
    c1.metric("Live Price", f"₹{live_rate:,}")
    c2.metric("Total Invested", f"₹{total_inv:,}")
    c3.metric("Gold Weight", f"{total_grams}g")
else:
    st.info(f"Log your entry. Current Market Price: ₹{live_rate}")
