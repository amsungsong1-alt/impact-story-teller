import streamlit as st

from modules import data_loader, metrics

st.set_page_config(page_title="Impact-Story-Teller", layout="wide")

with st.sidebar:
    st.header("Upload Data")
    uploaded_file = st.file_uploader("Upload an Excel or CSV file", type=["xlsx", "csv"])
    st.caption("A sample dataset is available at **data/sample_data.xlsx**.")

st.title("Impact-Story-Teller")

if uploaded_file is None:
    st.info("Upload a **.xlsx** or **.csv** file using the sidebar to get started.")
else:
    df, report = data_loader.load_data(uploaded_file)

    if report.get("read_error"):
        st.error(report["read_error"])
    else:
        if report["missing_columns"]:
            st.error(
                "**Missing expected columns:** " + ", ".join(report["missing_columns"])
            )
        if report["extra_columns"]:
            st.warning(
                "**Unrecognized columns (ignored):** " + ", ".join(report["extra_columns"])
            )

        st.success(f"Loaded **{len(df)}** rows.")

        st.header("KPIs")
        kpis = metrics.compute_kpis(df)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            kpi = kpis["total_enterprises"]
            if kpi["available"]:
                st.metric("Enterprises Supported", kpi["value"])
            else:
                st.metric("Enterprises Supported", "N/A")
                st.caption(kpi["reason"])

        with col2:
            kpi = kpis["total_jobs_created"]
            if kpi["available"]:
                st.metric("Jobs Created", kpi["value"])
            else:
                st.metric("Jobs Created", "N/A")
                st.caption(kpi["reason"])

        with col3:
            kpi = kpis["pct_women_led"]
            if kpi["available"]:
                st.metric("% Women-Led", f"{kpi['value']}%")
            else:
                st.metric("% Women-Led", "N/A")
                st.caption(kpi["reason"])

        with col4:
            kpi = kpis["regional_coverage"]
            if kpi["available"]:
                st.metric("Regions Covered", kpi["value"])
            else:
                st.metric("Regions Covered", "N/A")
                st.caption(kpi["reason"])

        st.header("Charts")
        st.info("Charts coming soon.")

        st.header("Data Gaps")
        if report["null_counts"]:
            gaps = {col: count for col, count in report["null_counts"].items() if count > 0}
            if gaps:
                st.write("**Missing values by column:**")
                st.table(
                    {"Column": list(gaps.keys()), "Missing Values": list(gaps.values())}
                )
            else:
                st.success("No missing values found in expected columns.")

        if report["malformed"]:
            st.write("**Malformed values by column:**")
            st.table(
                {
                    "Column": list(report["malformed"].keys()),
                    "Malformed Values": list(report["malformed"].values()),
                }
            )
