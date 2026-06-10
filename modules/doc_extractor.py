"""Extract tabular data from uploaded Word (.docx) and PDF files.

Returns the raw tables found in the document as DataFrames, without
attempting to map them to the expected schema - the user reviews the
extracted data and downloads it as XLSX/CSV, then uploads that file through
the main file uploader for validation.
"""

import pandas as pd


def extract_tables(uploaded_file):
    """Extract tables from an uploaded .docx or .pdf file.

    Returns (tables, error). tables is a list of DataFrames (one per
    detected table, in document order). error is a string describing why
    no tables could be extracted, or None.
    """
    name = uploaded_file.name.lower()

    try:
        if name.endswith(".docx"):
            return _extract_from_docx(uploaded_file), None
        elif name.endswith(".pdf"):
            return _extract_from_pdf(uploaded_file), None
        else:
            return [], "Unsupported file type. Please upload a .docx or .pdf file."
    except Exception as exc:
        return [], f"Could not read file: {exc}"


def _extract_from_docx(uploaded_file):
    from docx import Document

    doc = Document(uploaded_file)
    tables = []
    for table in doc.tables:
        rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        if len(rows) > 1:
            tables.append(_rows_to_dataframe(rows))
    return tables


def _extract_from_pdf(uploaded_file):
    import pdfplumber

    tables = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if table and len(table) > 1:
                    tables.append(_rows_to_dataframe(table))
    return tables


def _rows_to_dataframe(rows):
    """Build a DataFrame from raw table rows, tolerating ragged rows.

    Word and PDF tables can have rows with a different number of cells than
    the header (e.g. due to merged cells), which would otherwise raise a
    "columns passed, passed data had N columns" error from pandas.
    """
    rows = [["" if cell is None else str(cell).strip() for cell in row] for row in rows]

    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]

    header = _dedupe_columns(rows[0])
    return pd.DataFrame(rows[1:], columns=header)


def _dedupe_columns(header):
    seen = {}
    columns = []
    for i, name in enumerate(header):
        name = name if name else f"column_{i + 1}"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 0
        columns.append(name)
    return columns
