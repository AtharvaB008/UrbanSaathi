"""
UrbanSaathi — Ward Indicator Synchronization

Prepares ward facility counts and equal-ward
distribution gap scores for SQLite.

This module does not use population-based benchmarks.
"""

import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from modules.ward_facility_counts import build_ward_facility_counts


CATEGORY_COLUMNS = {
    "Healthcare": "healthcare_count",
    "Education": "education_count",
    "Parks": "parks_count",
    "Bus stops": "transport_count",
}


def prepare_ward_indicators():
    """
    Calculate ward-level facility counts and
    relative distribution gap scores.

    Returns a DataFrame without modifying SQLite.
    """

    wards = build_ward_facility_counts().copy()

    if wards.empty:
        raise ValueError("No ward data available.")

    if wards["KGISWardNo"].isna().any():
        raise ValueError("Ward numbers cannot be missing.")

    if wards["KGISWardNo"].duplicated().any():
        raise ValueError("Duplicate ward numbers detected.")

    ward_count = len(wards)
    score_columns = []

    for category, count_column in CATEGORY_COLUMNS.items():
        if wards[count_column].isna().any():
            raise ValueError(
                f"Missing facility counts for {category}."
            )

        if (wards[count_column] < 0).any():
            raise ValueError(
                f"Invalid negative facility counts for {category}."
            )

        total = float(wards[count_column].sum())
        expected = total / ward_count

        score_column = f"{count_column}_gap_score"
        score_columns.append(score_column)

        if total == 0:
            wards[score_column] = np.nan
        else:
            wards[score_column] = (
                ((expected - wards[count_column]) / expected) * 100
            ).clip(lower=0, upper=100)

    wards["overall_distribution_gap_score"] = wards[
        score_columns
    ].mean(axis=1, skipna=False)

    return wards

def sync_indicators_to_database():
    """
    Synchronize Nishu's ward-level facility indicators.

    Replaces only indicators managed by this synchronization.
    Does not modify complaints, wards, or facilities.
    """

    project_root = Path(__file__).resolve().parent.parent
    database_path = project_root / "database" / "urbansaathi.db"

    if not database_path.is_file():
        raise FileNotFoundError(
            "UrbanSaathi SQLite database not found."
        )

    wards = prepare_ward_indicators()

    if len(wards) != 60:
        raise ValueError("Expected exactly 60 wards.")

    source_date = datetime.now(
        timezone.utc
    ).date().isoformat()

    source_name = "UrbanSaathi Ward Facility Diagnostics"

    indicator_columns = {
        "healthcare_facility_count": (
            "healthcare_count", "facilities"
        ),
        "education_facility_count": (
            "education_count", "facilities"
        ),
        "parks_facility_count": (
            "parks_count", "facilities"
        ),
        "bus_stop_count": (
            "transport_count", "stops"
        ),
        "healthcare_distribution_gap_score": (
            "healthcare_count_gap_score", "score / 100"
        ),
        "education_distribution_gap_score": (
            "education_count_gap_score", "score / 100"
        ),
        "parks_distribution_gap_score": (
            "parks_count_gap_score", "score / 100"
        ),
        "bus_stop_distribution_gap_score": (
            "transport_count_gap_score", "score / 100"
        ),
        "overall_distribution_gap_score": (
            "overall_distribution_gap_score", "score / 100"
        ),
    }

    records = []

    for _, ward in wards.iterrows():
        ward_id = int(ward["KGISWardNo"])

        for indicator_name, (column, unit) in indicator_columns.items():
            value = ward[column]

            # Missing measurements must not become zero.
            if pd.isna(value):
                continue

            is_gap_score = indicator_name.endswith(
                "_gap_score"
            )

            calculation_method = (
                "Equal-ward benchmark: "
                "max(0, min(100, "
                "(citywide average - ward count) / "
                "citywide average * 100))."
                if is_gap_score
                else "Count of mapped OpenStreetMap facilities "
                     "assigned to exactly one ward."
            )

            if indicator_name == "overall_distribution_gap_score":
                calculation_method = (
                    "Arithmetic mean of four available "
                    "category distribution-gap scores."
                )

            records.append((
                ward_id,
                indicator_name,
                float(value),
                unit,
                source_name,
                source_date,
                calculation_method,
                (
                    "Mapped OpenStreetMap coverage only. "
                    "Not population-adjusted; does not measure "
                    "facility capacity, quality, or actual service need."
                ),
            ))

    # Validate everything before changing SQLite.
    if len(records) != 540:
        raise ValueError(
            f"Expected 540 indicators, prepared {len(records)}."
        )

    connection = sqlite3.connect(database_path)

    try:
        with connection:
            valid_wards = {
                row[0]
                for row in connection.execute(
                    "SELECT ward_id FROM wards"
                )
            }

            if not {
                record[0] for record in records
            }.issubset(valid_wards):
                raise ValueError(
                    "Indicator records contain unknown ward IDs."
                )

            connection.execute(
                "DELETE FROM indicators WHERE source = ?",
                (source_name,),
            )

            connection.executemany(
                """
                INSERT INTO indicators (
                    ward_id,
                    indicator_name,
                    value,
                    unit,
                    source,
                    reference_date,
                    calculation_method,
                    coverage_notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )

    finally:
        connection.close()

    return {
        "imported": len(records),
        "wards": len(wards),
        "source_date": source_date,
    }