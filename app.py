import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from ta.momentum import RSIIndicator

st.set_page_config(page_title="🧠 Ultimate Portfolio Analyzer", layout="centered")

st.title("📊 Ultimate Portfolio Analyzer (Live + AI)")
st.caption("Live prices • Real RSI • AI Rebalancing • Risk-based Strategy")

# -----------------------------
# Investor Profile
# -----------------------------
risk_profile = st.selectbox(
    "🧠 Select Investor Risk Profile",
    ["Conservative", "Moderate", "Aggressive"]
)

risk_rules = {
    "Conservative": {"sl": 0.92, "target": 1.10},
    "Moderate": {"sl": 0.90, "target": 1.20},
    "Aggressive": {"sl": 0.85, "target": 1.35}
}

uploaded_file = st.file_uploader("Upload Broker Holdings CSV", type=["csv"])

if uploaded_file:

    # -----------------------------
    # Read & detect header
    # -----------------------------
    raw = pd.read_csv(uploaded_file, header=None)
    header_row = next(
        (i for i in range(len(raw)) if raw.iloc[i].astype(str).str.contains("symbol", case=False).any()),
        None
    )

    if header_row is None:
        st.error("Invalid holdings file")
        st.stop()

    raw.columns = raw.iloc[header_row]
    df = raw.iloc[header_row + 1:].reset_index(drop=True)
    df.columns = [str(c).strip().lower() for c in df.columns]

    def col(key):
        return next(c for c in df.columns if key in c)

    df = df[[col("symbol"), col("qty"), col("avg"), col("ltp"), col("current")]]
    df.columns = ["Symbol", "Quantity", "BuyPrice", "CurrentPrice", "CurrentValue"]

    for c in df.columns[1:]:
        df[c] = df[c].astype(str).str.replace(",", "").astype(float)

    # -----------------------------
    # 🔴 Live Prices + RSI
    # -----------------------------
    st.subheader("🔴 Live Market Data")

    prices, rsis = [], []

    with st.spinner("Fetching live prices & RSI..."):
        for sym in df["Symbol"]:
            try:
                ticker = yf.Ticker(sym + ".NS")
                hist = ticker.history(period="3mo")
                close = hist["Close"]

                prices.append(close.iloc[-1])
                rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
                rsis.append(round(rsi, 2))
            except:
                prices.append(np.nan)
                rsis.append(np.nan)

    df["LivePrice"] = prices
    df["RSI"] = rsis

    # -----------------------------
    # Returns & Risk Levels
    # -----------------------------
    df["Return_%"] = (df["LivePrice"] - df["BuyPrice"]) / df["BuyPrice"] * 100

    sl = risk_rules[risk_profile]["sl"]
    tg = risk_rules[risk_profile]["target"]

    df["StopLoss"] = df["LivePrice"] * sl
    df["Target"] = df["LivePrice"] * tg

    # -----------------------------
    # 🤖 AI Rebalancing Logic
    # -----------------------------
    def ai_action(row):
        if row["RSI"] > 70:
            return "Reduce 🔻"
        elif row["RSI"] < 30:
            return "Add 🔼"
        elif row["Return_%"] > 25 and risk_profile == "Conservative":
            return "Book Profit 💰"
        else:
            return "Hold ⏸"

    df["AI_Action"] = df.apply(ai_action, axis=1)

    # -----------------------------
    # Sell Priority
    # -----------------------------
    df["SellScore"] = (df["RSI"] > 70) * 2 + (df["Return_%"] < -10)
    df["SellPriority"] = df["SellScore"].rank(ascending=False)

    # -----------------------------
    # Dashboard (Mobile Friendly)
    # -----------------------------
    st.metric("💰 Portfolio Value", f"₹{df['CurrentValue'].sum():,.0f}")
    st.metric("📊 Avg Return %", round(df["Return_%"].mean(), 2))

    with st.expander("📋 Stock-wise AI Analysis"):
        st.dataframe(
            df[[
                "Symbol", "LivePrice", "RSI", "Return_%",
                "StopLoss", "Target", "AI_Action", "SellPriority"
            ]].sort_values("SellPriority"),
            use_container_width=True
        )

    # -----------------------------
    # Charts
    # -----------------------------
    st.subheader("📈 RSI Levels")
    st.bar_chart(df.set_index("Symbol")["RSI"])

    # -----------------------------
    # Download
    # -----------------------------
    st.download_button(
        "📥 Download AI Portfolio Report",
        df.to_csv(index=False),
        "ai_portfolio_report.csv",
        "text/csv"
    )

else:
    st.info("Upload your holdings CSV to begin analysis")
