"""Load and validate uploaded enterprise-support data files.

Never fabricates or imputes values - any gaps or inconsistencies in the
source data are reported back so they can be surfaced to the user.
"""

import pandas as pd

EXPECTED_COLUMNS = [
    "program_name",
    "beneficiary_id",
    "gender",
    "region",
    "enterprise_stage",
    "jobs_created",
    "revenue_change",
    "date_supported",
    "support_type",
]

NUMERIC_COLUMNS = ["jobs_created", "revenue_change"]
DATE_COLUMNS = ["date_supported"]
EXPECTED_GENDER_VALUES = {"male", "female", "other"}


def validate_schema(df):
    """Build a report describing how well df matches the expected schema.

    Returns a dict with:
        missing_columns: expected columns not present in df
        extra_columns: columns present in df but not in the expected schema
        null_counts: {column: count of missing/blank values} for expected
            columns that are present
        malformed: {column: count of values that don't match the expected
            type/format} for expected columns that are present
    """
    columns = list(df.columns)

    missing_columns = [c for c in EXPECTED_COLUMNS if c not in columns]
    extra_columns = [c for c in columns if c not in EXPECTED_COLUMNS]

    null_counts = {}
    malformed = {}

    for col in EXPECTED_COLUMNS:
        if col not in columns:
            continue

        series = df[col]
        null_counts[col] = int(series.isna().sum())

        if col in NUMERIC_COLUMNS:
            non_null = series.dropna()
            bad = pd.to_numeric(non_null, errors="coerce").isna().sum()
            if bad:
                malformed[col] = int(bad)
        elif col in DATE_COLUMNS:
            non_null = series.dropna()
            bad = pd.to_datetime(non_null, errors="coerce").isna().sum()
            if bad:
                malformed[col] = int(bad)
        elif col == "gender":
            non_null = series.dropna().astype(str).str.strip().str.lower()
            bad = (~non_null.isin(EXPECTED_GENDER_VALUES)).sum()
            if bad:
                malformed[col] = int(bad)

    return {
        "missing_columns": missing_columns,
        "extra_columns": extra_columns,
        "null_counts": null_counts,
        "malformed": malformed,
    }


def load_data(uploaded_file):
    """Load an uploaded .xlsx or .csv file and validate it against the schema.

    Returns (df, report). If the file can't be read at all, df is None and
    report contains a "read_error" key describing the problem.
    """
    name = uploaded_file.name.lower()

    try:
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        else:
            return None, {"read_error": "Unsupported file type. Please upload a .xlsx or .csv file."}
    except Exception as exc:
        return None, {"read_error": f"Could not read file: {exc}"}

    report = validate_schema(df)
    return df, report
