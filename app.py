import streamlit as st
import pandas as pd

st.set_page_config(page_title="📊 Portfolio Analyzer", layout="wide")

st.title("📈 Portfolio Analyzer – Buy / Hold / Sell")
st.write("Upload your broker holdings CSV file")

# -----------------------------
# File Upload
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload Holdings CSV",
    type=["csv"]
)

if uploaded_file:

    # -----------------------------
    # Read & Clean File
    # -----------------------------
    raw = pd.read_csv(uploaded_file, header=None)

    raw.columns = raw.iloc[2]
    df = raw.iloc[3:].reset_index(drop=True)

    df = df[[
        "Symbol (21)",
        "Net Qty",
        "Avg. Price",
        "LTP",
        "Current Value",
        "Overall %"
    ]]

    df.columns = [
        "Symbol",
        "Quantity",
        "BuyPrice",
        "CurrentPrice",
        "CurrentValue",
        "Return_%"
    ]

    # -----------------------------
    # Data Cleaning
    # -----------------------------
    df["Quantity"] = pd.to_numeric(df["Quantity"])
    df["BuyPrice"] = pd.to_numeric(df["BuyPrice"])
    df["CurrentPrice"] = pd.to_numeric(df["CurrentPrice"])
    df["CurrentValue"] = pd.to_numeric(df["CurrentValue"])

    df["Return_%"] = (
        df["Return_%"]
        .str.replace("%", "")
        .str.replace(",", "")
        .astype(float)
    )

    # -----------------------------
    # Recommendation Logic
    # -----------------------------
    def recommend(row):
        if row["Return_%"] < -10:
            return "SELL ❌"
        elif -10 <= row["Return_%"] <= 10:
            return "HOLD ⏸"
        else:
            return "HOLD / ADD ✅"

    df["Recommendation"] = df.apply(recommend, axis=1)

    # -----------------------------
    # KPIs
    # -----------------------------
    total_value = df["CurrentValue"].sum()
    total_profit = (df["Return_%"] * df["CurrentValue"] / 100).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Portfolio Value", f"₹{total_value:,.0f}")
    col2.metric("📊 No. of Stocks", len(df))
    col3.metric("📈 Avg Return (%)", round(df["Return_%"].mean(), 2))

    st.divider()

    # -----------------------------
    # Filters
    # -----------------------------
    filter_option = st.selectbox(
        "Filter by Recommendation",
        ["All", "SELL ❌", "HOLD ⏸", "HOLD / ADD ✅"]
    )

    if filter_option != "All":
        df = df[df["Recommendation"] == filter_option]

    # -----------------------------
    # Table
    # -----------------------------
    st.subheader("📋 Stock-wise Recommendation")
    st.dataframe(
        df.sort_values("Return_%"),
        use_container_width=True
    )

    # -----------------------------
    # Charts
    # -----------------------------
    st.subheader("📊 Return Distribution")
    st.bar_chart(
        df.set_index("Symbol")["Return_%"]
    )

    # -----------------------------
    # Download
    # -----------------------------
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Recommendation CSV",
        csv,
        "portfolio_recommendations.csv",
        "text/csv"
    )

else:
    st.info("👆 Upload your holdings CSV file to begin analysis")
