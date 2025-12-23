import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from ta.momentum import RSIIndicator

# -------------------------------------------------
# Page Config (Mobile Friendly)
# -------------------------------------------------
st.set_page_config(
    page_title="Ultimate Portfolio Analyzer",
    layout="centered"
)

st.title("📊 Ultimate Portfolio Analyzer")
st.caption("Live Prices • Real RSI • AI Rebalancing • Risk-Based Strategy")

# -------------------------------------------------
# Investor Profile
# -------------------------------------------------
risk_profile = st.selectbox(
    "🧠 Select Investor Risk Profile",
    ["Conservative", "Moderate", "Aggressive"]
)

risk_rules = {
    "Conservative": {"sl": 0.92, "target": 1.10},
    "Moderate": {"sl": 0.90, "target": 1.20},
    "Aggressive": {"sl": 0.85, "target": 1.35}
}

# -------------------------------------------------
# File Upload
# -------------------------------------------------
uploaded_file = st.file_uploader(
    "📁 Upload Broker Holdings CSV",
    type=["csv"]
)

if not uploaded_file:
    st.info("👆 Upload your holdings CSV to begin")
    st.stop()

# -------------------------------------------------
# Read raw CSV & detect header
# -------------------------------------------------
raw = pd.read_csv(uploaded_file, header=None)

header_row = None
for i in range(len(raw)):
    if raw.iloc[i].astype(str).str.contains("symbol", case=False).any():
        header_row = i
        break

if header_row is None:
    st.error("❌ Could not detect holdings header row")
    st.stop()

raw.columns = raw.iloc[header_row]
df = raw.iloc[header_row + 1:].reset_index(drop=True)

df.columns = [str(c).strip().lower() for c in df.columns]

def find_col(keyword):
    for c in df.columns:
        if keyword in c:
            return c
    return None

required_cols = {
    "symbol": find_col("symbol"),
    "qty": find_col("qty"),
    "avg": find_col("avg"),
    "ltp": find_col("ltp"),
    "current": find_col("current")
}

if any(v is None for v in required_cols.values()):
    st.error("❌ Required columns missing in CSV")
    st.write("Detected columns:", df.columns.tolist())
    st.stop()

df = df[list(required_cols.values())]
df.columns = ["Symbol", "Quantity", "BuyPrice", "CurrentPrice", "CurrentValue"]

# -------------------------------------------------
# Clean numeric data
# -------------------------------------------------
for col in ["Quantity", "BuyPrice", "CurrentPrice", "CurrentValue"]:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", "")
        .astype(float)
    )

# -------------------------------------------------
# 🔴 Live Prices + REAL RSI (Yahoo Finance)
# -------------------------------------------------
st.subheader("🔴 Live Market Data")

live_prices = []
rsi_values = []

with st.spinner("Fetching live prices & RSI..."):
    for symbol in df["Symbol"]:
        try:
            ticker = yf.Ticker(symbol + ".NS")
            hist = ticker.history(period="3mo")

            if hist.empty:
                raise Exception("No NSE data")

            close = hist["Close"]
            price = close.iloc[-1]
            rsi = RSIIndicator(close, window=14).rsi().iloc[-1]

        except:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="3mo")
                close = hist["Close"]
                price = close.iloc[-1]
                rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
            except:
                price = np.nan
                rsi = np.nan

        live_prices.append(round(price, 2) if price == price else np.nan)
        rsi_values.append(round(rsi, 2) if rsi == rsi else np.nan)

df["LivePrice"] = live_prices
df["RSI"] = rsi_values

# -------------------------------------------------
# Returns, Stop Loss, Target
# -------------------------------------------------
df["Return_%"] = (df["LivePrice"] - df["BuyPrice"]) / df["BuyPrice"] * 100

sl = risk_rules[risk_profile]["sl"]
tg = risk_rules[risk_profile]["target"]

df["StopLoss"] = (df["LivePrice"] * sl).round(2)
df["Target"] = (df["LivePrice"] * tg).round(2)

# -------------------------------------------------
# 🤖 AI Rebalancing Suggestions
# -------------------------------------------------
def ai_action(row):
    if pd.isna(row["RSI"]):
        return "Data Unavailable ⚠️"
    if row["RSI"] > 70:
        return "Reduce / Book Profit 🔻"
    elif row["RSI"] < 30:
        return "Add More 🔼"
    elif row["Return_%"] > 25 and risk_profile == "Conservative":
        return "Book Partial Profit 💰"
    else:
        return "Hold ⏸"

df["AI_Action"] = df.apply(ai_action, axis=1)

# -------------------------------------------------
# Sell Priority Ranking
# -------------------------------------------------
df["SellScore"] = (
    (df["RSI"] > 70).astype(int) * 2 +
    (df["Return_%"] < -10).astype(int)
)

df["SellPriority"] = df["SellScore"].rank(
    ascending=False,
    method="dense"
)

# -------------------------------------------------
# Dashboard KPIs
# -------------------------------------------------
st.metric("💰 Portfolio Value", f"₹{df['CurrentValue'].sum():,.0f}")
st.metric("📊 Average Return %", round(df["Return_%"].mean(), 2))

# -------------------------------------------------
# Table View
# -------------------------------------------------
with st.expander("📋 Stock-wise AI Analysis"):
    st.dataframe(
        df[[
            "Symbol",
            "LivePrice",
            "RSI",
            "Return_%",
            "StopLoss",
            "Target",
            "AI_Action",
            "SellPriority"
        ]].sort_values("SellPriority"),
        use_container_width=True
    )

# -------------------------------------------------
# Charts
# -------------------------------------------------
st.subheader("📈 RSI Indicator")
st.bar_chart(df.set_index("Symbol")["RSI"])

# -------------------------------------------------
# Download Report
# -------------------------------------------------
st.download_button(
    "📥 Download Full AI Portfolio Report",
    df.to_csv(index=False),
    "ai_portfolio_report.csv",
    "text/csv"
)
