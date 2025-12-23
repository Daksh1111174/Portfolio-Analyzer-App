import streamlit as st
import pandas as pd

st.set_page_config(page_title="📊 Portfolio Analyzer", layout="wide")
st.title("📈 Portfolio Analyzer – Buy / Hold / Sell")

uploaded_file = st.file_uploader("Upload Holdings CSV", type=["csv"])

if uploaded_file:

    # -----------------------------
    # Read raw file
    # -----------------------------
    raw = pd.read_csv(uploaded_file, header=None)

    # -----------------------------
    # Find header row automatically
    # -----------------------------
    header_row = None
    for i in range(len(raw)):
        if raw.iloc[i].astype(str).str.contains("Symbol", case=False).any():
            header_row = i
            break

    if header_row is None:
        st.error("❌ Could not detect header row. Please upload valid holdings file.")
        st.stop()

    # -----------------------------
    # Create clean dataframe
    # -----------------------------
    raw.columns = raw.iloc[header_row]
    df = raw.iloc[header_row + 1:].reset_index(drop=True)

    # -----------------------------
    # Normalize column names
    # -----------------------------
    df.columns = [str(c).strip().lower() for c in df.columns]

    def find_col(keyword):
        for col in df.columns:
            if keyword in col:
                return col
        return None

    col_symbol = find_col("symbol")
    col_qty = find_col("qty")
    col_buy = find_col("avg")
    col_ltp = find_col("ltp")
    col_value = find_col("current")
    col_return = find_col("%")

    required = [col_symbol, col_qty, col_buy, col_ltp, col_value, col_return]
    if any(c is None for c in required):
        st.error("❌ Required columns not found in file")
        st.write("Detected columns:", df.columns.tolist())
        st.stop()

    df = df[required]
    df.columns = ["Symbol", "Quantity", "BuyPrice", "CurrentPrice", "CurrentValue", "Return_%"]

    # -----------------------------
    # Clean data
    # -----------------------------
    for col in ["Quantity", "BuyPrice", "CurrentPrice", "CurrentValue"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "")
            .astype(float)
        )

    df["Return_%"] = (
        df["Return_%"]
        .astype(str)
        .str.replace("%", "")
        .str.replace(",", "")
        .astype(float)
    )

    # -----------------------------
    # Recommendation logic
    # -----------------------------
    def recommend(r):
        if r < -10:
            return "SELL ❌"
        elif -10 <= r <= 10:
            return "HOLD ⏸"
        else:
            return "HOLD / ADD ✅"

    df["Recommendation"] = df["Return_%"].apply(recommend)

    # -----------------------------
    # KPIs
    # -----------------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Portfolio Value", f"₹{df['CurrentValue'].sum():,.0f}")
    col2.metric("📊 Stocks", len(df))
    col3.metric("📈 Avg Return %", round(df["Return_%"].mean(), 2))

    st.divider()

    # -----------------------------
    # Filters
    # -----------------------------
    choice = st.selectbox(
        "Filter Recommendation",
        ["All", "SELL ❌", "HOLD ⏸", "HOLD / ADD ✅"]
    )

    show_df = df if choice == "All" else df[df["Recommendation"] == choice]

    st.dataframe(
        show_df.sort_values("Return_%"),
        use_container_width=True
    )

    # -----------------------------
    # Chart
    # -----------------------------
    st.subheader("📊 Stock Returns")
    st.bar_chart(show_df.set_index("Symbol")["Return_%"])

    # -----------------------------
    # Download
    # -----------------------------
    st.download_button(
        "📥 Download CSV",
        show_df.to_csv(index=False),
        "portfolio_recommendations.csv",
        "text/csv"
    )

else:
    st.info("👆 Upload your broker holdings CSV to begin")
