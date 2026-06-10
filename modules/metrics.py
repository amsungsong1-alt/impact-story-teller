"""Compute headline KPIs from enterprise-support data.

Each KPI is only computed when the columns it depends on are present and
contain usable data. Otherwise it is marked unavailable with a reason,
rather than being filled in with a fabricated value.
"""

import pandas as pd


def compute_kpis(df):
    """Return a dict of KPI name -> {"available": bool, "value": ..., "reason": str}."""
    kpis = {}

    columns = list(df.columns)

    # Total enterprises supported (unique beneficiaries)
    if "beneficiary_id" in columns:
        ids = df["beneficiary_id"].dropna()
        if len(ids) > 0:
            kpis["total_enterprises"] = {"available": True, "value": int(ids.nunique())}
        else:
            kpis["total_enterprises"] = {"available": False, "reason": "No beneficiary_id values found"}
    else:
        kpis["total_enterprises"] = {"available": False, "reason": "beneficiary_id column missing"}

    # Total jobs created
    if "jobs_created" in columns:
        values = pd.to_numeric(df["jobs_created"], errors="coerce").dropna()
        if len(values) > 0:
            kpis["total_jobs_created"] = {"available": True, "value": int(values.sum())}
        else:
            kpis["total_jobs_created"] = {"available": False, "reason": "No usable jobs_created values found"}
    else:
        kpis["total_jobs_created"] = {"available": False, "reason": "jobs_created column missing"}

    # % women-led
    if "gender" in columns:
        gender = df["gender"].dropna().astype(str).str.strip().str.lower()
        if len(gender) > 0:
            women_led = gender.str.contains("female|woman|women", regex=True).sum()
            pct = round(100 * women_led / len(gender), 1)
            kpis["pct_women_led"] = {"available": True, "value": pct}
        else:
            kpis["pct_women_led"] = {"available": False, "reason": "No gender values found"}
    else:
        kpis["pct_women_led"] = {"available": False, "reason": "gender column missing"}

    # Regional coverage
    if "region" in columns:
        regions = df["region"].dropna().astype(str).str.strip()
        regions = regions[regions != ""]
        if len(regions) > 0:
            unique_regions = sorted(regions.unique())
            kpis["regional_coverage"] = {
                "available": True,
                "value": len(unique_regions),
                "regions": unique_regions,
            }
        else:
            kpis["regional_coverage"] = {"available": False, "reason": "No region values found"}
    else:
        kpis["regional_coverage"] = {"available": False, "reason": "region column missing"}

    return kpis
