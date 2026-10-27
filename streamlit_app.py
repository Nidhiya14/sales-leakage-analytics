from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="Sales Leakage Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "output" / "leakage_results.csv"
SALES = ROOT / "data" / "simulated_sales.csv"
SAMPLE = ROOT / "data" / "scraped_products.csv"

@st.cache_data
def load_csv(path_string, modified_time):
    return pd.read_csv(path_string)

def load_data():
    # modified_time makes Streamlit reload after a file is updated.
    for path in (RESULTS, SALES, SAMPLE):
        if path.exists():
            return load_csv(str(path), path.stat().st_mtime), path.name
    return pd.DataFrame(), None

def ensure_columns(df):
    df = df.copy()
    defaults = {
        "product_name": "Unknown product",
        "region": "Not specified",
        "priority": "Unclassified",
        "root_cause": "No explanation available",
        "discount_pct": 0,
        "profit_gbp": 0,
        "revenue_gbp": 0,
        "estimated_recovery_gbp": 0,
        "leakage_score": 0,
        "units_sold": 0,
        "zscore_flag": 0,
        "isolation_forest_flag": 0,
        "price_gbp": 0,
        "selling_price_gbp": 0,
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default
    for col in ["discount_pct", "profit_gbp", "revenue_gbp", "estimated_recovery_gbp",
                "leakage_score", "units_sold", "zscore_flag", "isolation_forest_flag",
                "price_gbp", "selling_price_gbp"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["priority"] = df["priority"].astype(str)
    df["product_name"] = df["product_name"].astype(str)
    df["region"] = df["region"].astype(str)
    df["root_cause"] = df["root_cause"].astype(str)
    return df

st.title(" Sales Leakage Detection & Revenue Opportunity Analytics")
st.caption("Web scraping • Hadoop HDFS storage • Data mining • Interactive dashboard")
st.info(
    "Academic demo: product information may be scraped from a practice website, while sales, "
    "cost, discount, region and recovery fields are simulated. These are not real company sales."
)

if st.button(" Refresh data"):
    st.cache_data.clear()
    st.rerun()

df_raw, source_name = load_data()
if df_raw.empty:
    st.error("No CSV data found. Run the data pipeline first or place a results CSV in output/leakage_results.csv.")
    st.code("python src/scrape_products.py\npython src/create_sales_dataset.py\npython src/analyze_leakage.py\nstreamlit run streamlit_app.py")
    st.stop()

df = ensure_columns(df_raw)
st.caption(f"Data source loaded: `{source_name}` · {len(df):,} rows")

# Sidebar filters
st.sidebar.header("Dashboard Filters")
regions = sorted(df["region"].dropna().unique().tolist())
priorities = sorted(df["priority"].dropna().unique().tolist())
products = sorted(df["product_name"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
selected_priorities = st.sidebar.multiselect("Priority", priorities, default=priorities)
selected_products = st.sidebar.multiselect("Product", products, default=products)

filtered = df[
    df["region"].isin(selected_regions)
    & df["priority"].isin(selected_priorities)
    & df["product_name"].isin(selected_products)
].copy()

flagged_mask = (
    (pd.to_numeric(filtered["zscore_flag"], errors="coerce").fillna(0) == 1)
    | (pd.to_numeric(filtered["isolation_forest_flag"], errors="coerce").fillna(0) == 1)
)
flagged_count = int(flagged_mask.sum())
total_revenue = float(filtered["revenue_gbp"].sum())
total_profit = float(filtered["profit_gbp"].sum())
potential_recovery = float(filtered["estimated_recovery_gbp"].sum())
avg_score = float(filtered["leakage_score"].mean()) if not filtered.empty else 0.0
critical_count = int((filtered["priority"].str.lower() == "critical").sum())

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Revenue", f"£{total_revenue:,.2f}")
c2.metric("Total Profit", f"£{total_profit:,.2f}")
c3.metric("Potential Recovery*", f"£{potential_recovery:,.2f}")
c4.metric("Flagged Records", f"{flagged_count:,}")
c5.metric("Average Leakage Score", f"{avg_score:.1f}/100")

st.caption("*Illustrative recovery estimate from the demo's simulated sales data; not money already recovered.")

if filtered.empty:
    st.warning("No rows match the selected filters. Select one or more values in the sidebar.")
    st.stop()

# Charts row 1
left, right = st.columns(2)
with left:
    revenue_df = (filtered.groupby("product_name", as_index=False)["revenue_gbp"].sum()
                  .sort_values("revenue_gbp", ascending=False).head(10))
    fig = px.bar(revenue_df, x="revenue_gbp", y="product_name", orientation="h",
                 title="Top 10 Products by Revenue", labels={"revenue_gbp": "Revenue (£)", "product_name": "Product"})
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig, use_container_width=True)

with right:
    recovery_df = (filtered.groupby("product_name", as_index=False)["estimated_recovery_gbp"].sum()
                   .sort_values("estimated_recovery_gbp", ascending=False).head(10))
    fig = px.bar(recovery_df, x="product_name", y="estimated_recovery_gbp",
                 title="Top 10 Products by Potential Recovery",
                 labels={"estimated_recovery_gbp": "Estimated recovery (£)", "product_name": "Product"})
    fig.update_layout(xaxis_tickangle=-35, margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig, use_container_width=True)

# Charts row 2
left, right = st.columns(2)
with left:
    priority_df = filtered.groupby("priority", as_index=False).size().rename(columns={"size": "records"})
    fig = px.pie(priority_df, names="priority", values="records", hole=0.45,
                 title="Records by Priority")
    st.plotly_chart(fig, use_container_width=True)

with right:
    cause_df = filtered["root_cause"].value_counts().head(8).rename_axis("root_cause").reset_index(name="records")
    fig = px.bar(cause_df, x="records", y="root_cause", orientation="h",
                 title="Most Common Root-Cause Explanations",
                 labels={"records": "Number of records", "root_cause": "Root cause"})
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.subheader(" Sales Leakage Priority Board")
st.write("Records are sorted by leakage score and estimated recovery to help prioritize investigation.")
priority_board = filtered.sort_values(
    ["leakage_score", "estimated_recovery_gbp"], ascending=False
).copy()
display_cols = [
    c for c in ["product_name", "region", "discount_pct", "revenue_gbp", "profit_gbp",
                "leakage_score", "priority", "root_cause", "estimated_recovery_gbp"]
    if c in priority_board.columns
]
st.dataframe(
    priority_board[display_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "discount_pct": st.column_config.NumberColumn("Discount (%)", format="%.1f"),
        "revenue_gbp": st.column_config.NumberColumn("Revenue (£)", format="£%.2f"),
        "profit_gbp": st.column_config.NumberColumn("Profit (£)", format="£%.2f"),
        "leakage_score": st.column_config.ProgressColumn("Leakage Score", min_value=0, max_value=100, format="%.1f"),
        "estimated_recovery_gbp": st.column_config.NumberColumn("Potential Recovery (£)", format="£%.2f"),
    },
)

csv_bytes = priority_board.to_csv(index=False).encode("utf-8")
st.download_button(
    " Download filtered priority board as CSV",
    data=csv_bytes,
    file_name="filtered_leakage_priority_board.csv",
    mime="text/csv",
)

with st.expander("View raw data"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Pipeline: Web Scraping → CSV → Data Mining (Z-score + Isolation Forest) → Hadoop HDFS → Streamlit Dashboard")
