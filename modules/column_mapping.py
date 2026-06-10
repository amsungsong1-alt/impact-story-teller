"""Suggest mappings from extracted document columns to the expected schema.

Uses a built-in set of keyword synonyms plus any synonyms learned from
previous uploads (persisted to data/column_synonyms.json) to suggest a
mapping from raw column headers to the expected schema columns. Suggestions
are always presented to the user for review before being applied - nothing
is renamed automatically, and nothing is learned unless the user confirms it.
"""

import json
import os
import re

from modules.data_loader import EXPECTED_COLUMNS

SYNONYMS_PATH = os.path.join("data", "column_synonyms.json")

DEFAULT_SYNONYMS = {
    "program_name": [
        "program name", "programme name", "program", "programme",
        "project name", "initiative", "initiative name",
    ],
    "beneficiary_id": [
        "beneficiary id", "beneficiary", "enterprise id", "enterprise name",
        "company id", "business id", "participant id", "id",
    ],
    "gender": ["gender", "sex", "owner gender", "gender of owner"],
    "region": ["region", "location", "province", "state", "district", "area", "county"],
    "enterprise_stage": [
        "enterprise stage", "business stage", "stage", "growth stage", "maturity stage",
    ],
    "jobs_created": [
        "jobs created", "jobs", "employment created", "new jobs", "number of jobs created",
    ],
    "revenue_change": [
        "revenue change", "revenue growth", "change in revenue", "income change",
        "revenue increase", "growth in revenue",
    ],
    "date_supported": ["date supported", "support date", "date of support", "date"],
    "support_type": [
        "support type", "type of support", "intervention type", "intervention", "assistance type",
    ],
}


def _normalize(text):
    text = text.lower().strip()
    text = re.sub(r"[_\-/]+", " ", text)
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_synonyms():
    """Return {expected_column: [synonym, ...]}, defaults merged with learned synonyms."""
    synonyms = {col: list(values) for col, values in DEFAULT_SYNONYMS.items()}

    if os.path.exists(SYNONYMS_PATH):
        try:
            with open(SYNONYMS_PATH, "r", encoding="utf-8") as f:
                learned = json.load(f)
        except (OSError, json.JSONDecodeError):
            learned = {}

        for col, values in learned.items():
            if col not in synonyms:
                continue
            for value in values:
                if value not in synonyms[col]:
                    synonyms[col].append(value)

    return synonyms


def save_synonym(expected_column, header_text):
    """Persist a newly learned header -> expected_column association, if new."""
    if expected_column not in EXPECTED_COLUMNS:
        return

    normalized = _normalize(header_text)
    if not normalized or normalized in DEFAULT_SYNONYMS.get(expected_column, []):
        return

    learned = {}
    if os.path.exists(SYNONYMS_PATH):
        try:
            with open(SYNONYMS_PATH, "r", encoding="utf-8") as f:
                learned = json.load(f)
        except (OSError, json.JSONDecodeError):
            learned = {}

    values = learned.setdefault(expected_column, [])
    if normalized not in values:
        values.append(normalized)
        os.makedirs(os.path.dirname(SYNONYMS_PATH), exist_ok=True)
        with open(SYNONYMS_PATH, "w", encoding="utf-8") as f:
            json.dump(learned, f, indent=2, sort_keys=True)


def suggest_mapping(columns):
    """Return {raw_column: expected_column or None}, a best-guess mapping."""
    synonyms = load_synonyms()
    mapping = {}

    for col in columns:
        normalized = _normalize(col)
        match = None

        # Prefer exact matches against known synonyms / column names.
        for expected_col, values in synonyms.items():
            candidates = values + [expected_col.replace("_", " ")]
            if normalized in candidates:
                match = expected_col
                break

        # Fall back to substring matches.
        if match is None:
            for expected_col, values in synonyms.items():
                candidates = values + [expected_col.replace("_", " ")]
                if any(c and (c in normalized or normalized in c) for c in candidates):
                    match = expected_col
                    break

        mapping[col] = match

    return mapping
