import streamlit as st
import pandas as pd

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="Supply Chain Fulfillment Dashboard",
    layout="wide"
)

# ---------------------------
# Load data
# ---------------------------
prod_df = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vQdXkqjpQkKY9ClQkRr30RsrbBhytn7sVR-N1TZN2wP7M_GYebkK5HU46p20j6VTIyEiTi8IXZBY7Aj", parse_dates=["eventDate"])
deliv_df = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vQVjgekM5TgKySYpBFbvjgjtasnPKp9mh0Oe-2UOQ01A8bWrWrPLh79-ERPJJkwzQSxmiqagVMxqjdP", parse_dates=["deliveredDate"])

# Filter 2025
prod_df = prod_df[prod_df["eventDate"].dt.year == 2025]
deliv_df = deliv_df[deliv_df["deliveredDate"].dt.year == 2025]

# ---------------------------
# Merge supplier into production
# ---------------------------
joined_df = prod_df.merge(
    deliv_df[
        ["soReference", "supplier", "delivered_on-time", "delivery_country_code", "deliveredDate"]
    ],
    left_on="salesOrderReference",
    right_on="soReference",
    how="left"
)
joined_df["supplier"] = joined_df["supplier"].fillna("UNKNOWN")

# ---------------------------
# Sidebar filters
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
prod_ot = joined_df["producedOnTime"].mean()
del_ot = deliv_df["delivered_on-time"].mean()

PROD_SLA = 0.95
DEL_SLA = 0.95

def kpi_color(value, sla):
    return "green" if value >= sla else "red"

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
# Monthly vs YTD logic
# ---------------------------
prod_df["month"] = prod_df["eventDate"].dt.month
deliv_df["month"] = deliv_df["deliveredDate"].dt.month

monthly_prod = prod_df.groupby("month")["producedOnTime"].mean().reset_index()
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
        monthly_perf.set_index("month")[["producedOnTime_prod", "delivered_on-time_deliv"]]
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
    Orders=("salesOrderReference", "count"),
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
    Orders=("soReference", "count"),
    Delivered_On_Time=("delivered_on-time", "mean")
).reset_index().sort_values("Delivered_On_Time", ascending=False)

st.dataframe(
    country_perf.style.format({"Delivered_On_Time": "{:.0%}"})
)

# ---------------------------
# Footer
# ---------------------------
st.caption("Built with Python, SQL logic, and Streamlit | Portfolio-ready analytics")
