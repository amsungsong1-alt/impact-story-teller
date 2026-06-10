import io

import pandas as pd
import streamlit as st

from modules import column_mapping, data_loader, doc_extractor, metrics

st.set_page_config(page_title="Impact-Story-Teller", layout="wide")

with st.sidebar:
    st.header("Extract from Word/PDF")
    st.caption("Upload a Word or PDF document containing a data table to convert it to XLSX/CSV.")
    doc_file = st.file_uploader("Upload a .docx or .pdf file", type=["docx", "pdf"], key="doc_upload")

    if doc_file is not None:
        tables, extract_error = doc_extractor.extract_tables(doc_file)

        if extract_error:
            st.error(extract_error)
        elif not tables:
            st.warning("No tables were found in this document.")
        else:
            if len(tables) > 1:
                table_index = st.selectbox(
                    "Multiple tables found - choose one to convert",
                    range(len(tables)),
                    format_func=lambda i: f"Table {i + 1} ({tables[i].shape[0]} rows x {tables[i].shape[1]} cols)",
                )
            else:
                table_index = 0

            extracted_df = tables[table_index]
            st.dataframe(extracted_df.head(10))

            raw_columns = extracted_df.columns.tolist()
            suggested = column_mapping.suggest_mapping(raw_columns)

            # Reverse the suggested raw_col -> expected_col mapping so each
            # expected column defaults to the raw column that best matches it.
            suggested_reverse = {}
            for raw_col, expected_col in suggested.items():
                suggested_reverse.setdefault(expected_col, raw_col)

            matched = sum(1 for v in suggested_reverse.values() if v is not None)
            st.caption(
                f"Recognized {matched} of {len(data_loader.EXPECTED_COLUMNS)} expected "
                "columns automatically."
            )

            options = ["(none)"] + raw_columns

            with st.expander("Adjust column mapping"):
                expected_choices = {}
                for expected_col in data_loader.EXPECTED_COLUMNS:
                    default = suggested_reverse.get(expected_col)
                    default_index = options.index(default) if default in options else 0
                    expected_choices[expected_col] = st.selectbox(
                        f"'{expected_col}' comes from",
                        options,
                        index=default_index,
                        key=f"map_{table_index}_{expected_col}",
                    )

            rename_map = {}
            seen_sources = {}
            for expected_col, raw_col in expected_choices.items():
                if raw_col == "(none)":
                    continue
                if raw_col in seen_sources:
                    st.warning(
                        f"'{raw_col}' is mapped to both '{seen_sources[raw_col]}' and "
                        f"'{expected_col}'. Using it for '{seen_sources[raw_col]}' and "
                        f"leaving '{expected_col}' unmapped."
                    )
                    continue
                seen_sources[raw_col] = expected_col
                rename_map[raw_col] = expected_col

            mapped_df = extracted_df.rename(columns=rename_map)

            if st.button("Remember this mapping for future uploads", key=f"learn_{table_index}"):
                for raw_col, expected_col in rename_map.items():
                    column_mapping.save_synonym(expected_col, raw_col)
                st.success("Mapping saved. Future uploads with these column names will be recognized automatically.")

            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                mapped_df.to_excel(writer, index=False)

            st.download_button(
                "Download as XLSX",
                data=excel_buffer.getvalue(),
                file_name="extracted_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            st.download_button(
                "Download as CSV",
                data=mapped_df.to_csv(index=False).encode("utf-8"),
                file_name="extracted_data.csv",
                mime="text/csv",
            )

            st.caption("Download the file above, then upload it below to view KPIs.")

    st.divider()

    st.header("Upload Data")
    uploaded_file = st.file_uploader("Upload an Excel or CSV file", type=["xlsx", "csv"])

    st.caption("A sample dataset is available below.")
    with open("data/sample_data.xlsx", "rb") as f:
        st.download_button(
            label="Download sample_data.xlsx",
            data=f,
            file_name="sample_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

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
