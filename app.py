import streamlit as st
import pandas as pd

st.set_page_config(page_title="Supply Chain Dashboard", layout="wide")

# ===========================
# DATA SOURCES
# ===========================
PROD_URL = "https://docs.google.com/spreadsheets/d/1s928UrG19mxzVKWex31TJLu3c_jfdtfvxbgjYPYsWVk/gviz/tq?tqx=out:csv&sheet=produced_on_time"
DELIV_URL = "https://docs.google.com/spreadsheets/d/13AUingDUvNEhDpvJviIvs6wZr_c9Ifb6OYeFHN8tK-k/gviz/tq?tqx=out:csv&sheet=delivered_on_time"

# ===========================
# LOAD DATA (SAFE)
# ===========================
@st.cache_data(ttl=300)
def load_data():
    prod = pd.read_csv(PROD_URL)
    deliv = pd.read_csv(DELIV_URL)

    # Normalize headers safely
    prod.columns = (
        prod.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    deliv.columns = (
        deliv.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    return prod, deliv


prod_df, deliv_df = load_data()

# ===========================
# DEBUG VIEW (TEMPORARY)
# ===========================
st.write("✅ Production Columns:", prod_df.columns.tolist())
st.write("✅ Delivery Columns:", deliv_df.columns.tolist())

# ===========================
# REQUIRED COLUMN CHECKS
# ===========================
required_prod_cols = {"eventdate", "salesorderreference", "producedontime"}
required_deliv_cols = {
    "soreference",
    "supplier",
    "delivereddate",
    "delivered_on_time",
    "delivery_country_code",
}

if not required_prod_cols.issubset(prod_df.columns):
    st.error("❌ Missing required PRODUCTION columns")
    st.stop()

if not required_deliv_cols.issubset(deliv_df.columns):
    st.error("❌ Missing required DELIVERY columns")
    st.stop()

# ===========================
# DATE PARSING
# ===========================
prod_df["eventdate"] = pd.to_datetime(prod_df["eventdate"], errors="coerce")
deliv_df["delivereddate"] = pd.to_datetime(deliv_df["delivereddate"], errors="coerce")

# Rename for business meaning
deliv_df.rename(columns={"delivereddate": "delivery"}, inplace=True)

# Filter 2025 only
prod_df = prod_df[prod_df["eventdate"].dt.year == 2025]
deliv_df = deliv_df[deliv_df["delivery"].dt.year == 2025]

# ===========================
# MERGE
# ===========================
joined_df = prod_df.merge(
    deliv_df[
        [
            "soreference",
            "supplier",
            "delivered_on_time",
            "delivery_country_code",
            "delivery",
        ]
    ],
    left_on="salesorderreference",
    right_on="soreference",
    how="left",
)

joined_df["supplier"] = joined_df["supplier"].fillna("UNKNOWN")

# ===========================
# KPI CALCULATIONS
# ===========================
prod_ot = joined_df["producedontime"].mean()
del_ot = deliv_df["delivered_on_time"].mean()

# ===========================
# UI
# ===========================
st.title("📦 Supply Chain Fulfillment Dashboard — 2025")

k1, k2 = st.columns(2)

k1.metric(
    "On-Time Production",
    f"{prod_ot:.0%}" if pd.notna(prod_ot) else "N/A",
)

k2.metric(
    "On-Time Delivery",
    f"{del_ot:.0%}" if pd.notna(del_ot) else "N/A",
)

# ===========================
# MONTHLY TREND
# ===========================
prod_df["month"] = prod_df["eventdate"].dt.month
deliv_df["month"] = deliv_df["delivery"].dt.month

monthly_prod = prod_df.groupby("month")["producedontime"].mean()
monthly_del = deliv_df.groupby("month")["delivered_on_time"].mean()

trend_df = pd.concat([monthly_prod, monthly_del], axis=1)
trend_df.columns = ["Produced On Time", "Delivered On Time"]

st.subheader("📈 Monthly Performance Trend")
st.line_chart(trend_df)

# ===========================
# SUPPLIER PERFORMANCE
# ===========================
st.subheader("🏭 Supplier Performance")

supplier_perf = (
    joined_df.groupby("supplier")
    .agg(
        Orders=("salesorderreference", "count"),
        Delivered_On_Time=("delivered_on_time", "mean"),
    )
    .sort_values("Delivered_On_Time", ascending=False)
)

st.dataframe(supplier_perf.style.format({"Delivered_On_Time": "{:.0%}"}))

# ===========================
# COUNTRY PERFORMANCE
# ===========================
st.subheader("🌍 Delivery Country Performance")

country_perf = (
    deliv_df.groupby("delivery_country_code")
    .agg(
        Orders=("soreference", "count"),
        Delivered_On_Time=("delivered_on_time", "mean"),
    )
    .sort_values("Delivered_On_Time", ascending=False)
)

st.dataframe(country_perf.style.format({"Delivered_On_Time": "{:.0%}"}))



