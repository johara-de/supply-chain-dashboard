import streamlit as st
import pandas as pd

# ---------------------------
# URLs
# ---------------------------
PROD_URL = "https://docs.google.com/spreadsheets/d/1s928UrG19mxzVKWex31TJLu3c_jfdtfvxbgjYPYsWVk/gviz/tq?tqx=out:csv&sheet=production_on_time"
DELIV_URL = "https://docs.google.com/spreadsheets/d/1s928UrG19mxzVKWex31TJLu3c_jfdtfvxbgjYPYsWVk/gviz/tq?tqx=out:csv&sheet=delivered_on_time"

# ---------------------------
# Load Data
# ---------------------------
@st.cache_data(ttl=300)
def load_data():
    # Load CSVs
    prod = pd.read_csv(PROD_URL)
    deliv = pd.read_csv(DELIV_URL)

    # Normalize column names
    prod.columns = prod.columns.str.strip().str.replace(" ", "_").str.lower()
    deliv.columns = deliv.columns.str.strip().str.replace(" ", "_").str.lower()

    # Debug: check column names
    # st.write("Prod columns:", prod.columns.tolist())
    # st.write("Deliv columns:", deliv.columns.tolist())

    # Parse dates
    prod["eventdate"] = pd.to_datetime(prod["eventdate"], errors="coerce")
    # Adjusted to actual normalized column name from Google Sheet
    deliv["delivereddate"] = pd.to_datetime(deliv["delivereddate"], errors="coerce")

    # Filter for 2025
    prod = prod[prod["eventdate"].dt.year == 2025]
    deliv = deliv[deliv["delivereddate"].dt.year == 2025]

    return prod, deliv

prod_df, deliv_df = load_data()

# ---------------------------
# Merge supplier info into production
# ---------------------------
joined_df = prod_df.merge(
    deliv_df[["soreference", "supplier", "delivered_on-time", "delivery_country_code", "delivereddate"]],
    left_on="salesorderreference",
    right_on="soreference",
    how="left"
)
joined_df["supplier"] = joined_df["supplier"].fillna("UNKNOWN")

# ---------------------------
# Sidebar Filters
# ---------------------------
st.sidebar.header("Filters")

supplier_filter = st.sidebar.multiselect(
    "Supplier",
    options=sorted(joined_df["supplier"].unique()),
    default=sorted(joined_df["supplier"].unique())
)

country_filter = st.sidebar.multiselect(
    "Delivery Country",
    options=sorted(deliv_df["delivery_country_code"].dropna().unique()),
    default=sorted(deliv_df["delivery_country_code"].dropna().unique())
)

view_mode = st.sidebar.radio(
    "View Mode",
    ["YTD", "Monthly"]
)

# Apply filters
joined_df = joined_df[joined_df["supplier"].isin(supplier_filter)]
deliv_df = deliv_df[deliv_df["delivery_country_code"].isin(country_filter)]

# ---------------------------
# KPI calculations
# ---------------------------
prod_ot = joined_df["producedontime"].mean()
del_ot = deliv_df["delivered_on-time"].mean()

PROD_SLA = 0.95
DEL_SLA = 0.95

# ---------------------------
# Header
# ---------------------------
st.title("📦 Supply Chain Fulfillment Dashboard — 2025")
st.caption("Production & Delivery Performance | Supplier & Country Analytics")

# ---------------------------
# KPI Cards
# ---------------------------
kpi1, kpi2 = st.columns(2)

kpi1.metric(
    "Production On-Time",
    f"{prod_ot:.0%}",
    delta=f"{prod_ot - PROD_SLA:.0%} vs SLA",
    delta_color="normal" if prod_ot >= PROD_SLA else "inverse"
)

kpi2.metric(
    "Delivered On-Time",
    f"{del_ot:.0%}",
    delta=f"{del_ot - DEL_SLA:.0%} vs SLA",
    delta_color="normal" if del_ot >= DEL_SLA else "inverse"
)

# ---------------------------
# Monthly vs YTD
# ---------------------------
prod_df["month"] = prod_df["eventdate"].dt.month
deliv_df["month"] = deliv_df["delivereddate"].dt.month

monthly_prod = prod_df.groupby("month")["producedontime"].mean().reset_index()
monthly_del = deliv_df.groupby("month")["delivered_on-time"].mean().reset_index()

monthly_perf = monthly_prod.merge(
    monthly_del, on="month", suffixes=("_prod", "_deliv")
)

# ---------------------------
# Performance Trend
# ---------------------------
st.subheader("Fulfillment Performance Trend")

if view_mode == "Monthly":
    st.line_chart(
        monthly_perf.set_index("month")[["producedontime_prod", "delivered_on-time_deliv"]]
    )
else:
    ytd_df = pd.DataFrame({
        "Metric": ["Production On-Time", "Delivered On-Time"],
        "YTD %": [prod_ot, del_ot]
    })
    st.table(ytd_df.style.format({"YTD %": "{:.0%}"}))

# ---------------------------
# Supplier Performance
# ---------------------------
st.subheader("Supplier Performance")

supplier_perf = joined_df.groupby("supplier").agg(
    Orders=("salesorderreference", "count"),
    Delivered_On_Time=("delivered_on-time", "mean")
).reset_index().sort_values("Delivered_On_Time", ascending=False)

st.dataframe(
    supplier_perf.style.format({"Delivered_On_Time": "{:.0%}"})
)

# ---------------------------
# Country Performance
# ---------------------------
st.subheader("Delivery Country Performance")

country_perf = deliv_df.groupby("delivery_country_code").agg(
    Orders=("soreference", "count"),
    Delivered_On_Time=("delivered_on-time", "mean")
).reset_index().sort_values("Delivered_On_Time", ascending=False)

st.dataframe(
    country_perf.style.format({"Delivered_On_Time": "{:.0%}"})
)

# ---------------------------
# Footer
# ---------------------------
st.caption("Built with Python, SQL logic, and Streamlit | Portfolio-ready analytics")

