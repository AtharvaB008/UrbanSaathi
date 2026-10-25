
"""Deterministic ward-level benchmarks and investment-priority scores.

This module calculates relative facility-distribution gaps.
It does not claim to measure official service adequacy.
"""

from collections.abc import Mapping

import numpy as np
import pandas as pd


DEFAULT_FACILITY_COLUMNS = {
    "healthcare": "healthcare_count",
    "education": "education_count",
    "parks": "parks_count",
    "transport": "transport_count",
}


def expected_facilities(
    city_facility_total: float,
    ward_population: float,
    city_population: float,
) -> float:
    """Calculate a ward's population-proportional facility benchmark."""
    values = [city_facility_total, ward_population, city_population]

    if not all(np.isfinite(value) for value in values):
        raise ValueError("Benchmark inputs must be finite numbers.")

    if any(value < 0 for value in values):
        raise ValueError("Benchmark inputs cannot be negative.")

    if city_population <= 0:
        raise ValueError("City population must be greater than zero.")

    return city_facility_total * ward_population / city_population


def facilities_per_10000(
    facility_count: float,
    population: float,
) -> float:
    """Calculate facilities per 10,000 residents."""
    if not np.isfinite(facility_count) or not np.isfinite(population):
        raise ValueError("Inputs must be finite numbers.")

    if facility_count < 0 or population < 0:
        raise ValueError("Inputs cannot be negative.")

    if population == 0:
        return np.nan

    return facility_count / population * 10_000


def _valid_number(value):
    """Return True for a finite, non-negative numeric value."""
    try:
        return bool(np.isfinite(value) and value >= 0)
    except (TypeError, ValueError):
        return False


def build_ward_diagnostics(
    wards: pd.DataFrame,
    ward_id_col: str = "KGISWardID",
    population_col: str = "population",
    facility_columns: Mapping[str, str] | None = None,
    weights: Mapping[str, float] | None = None,
) -> pd.DataFrame:
    """Build ward-level benchmarks and transparent priority scores.

    Required input columns:
        ward_id_col, population_col, and one column per facility category.

    Default facility columns:
        healthcare_count, education_count, parks_count, transport_count.

    Missing values are never silently converted to zero. If a category
    has missing counts, its benchmark and scores are unavailable for
    every ward because the citywide category total is unknown.

    Priority scores range from 0 to 100:
        0   = no measured shortfall against the relative benchmark
        100 = zero facilities where the expected count is positive

    Scores measure relative distribution gaps, not service adequacy.
    """
    if wards.empty:
        raise ValueError("Ward data is empty.")

    columns = dict(facility_columns or DEFAULT_FACILITY_COLUMNS)
    categories = list(columns)

    if not categories:
        raise ValueError("At least one facility category is required.")

    required = [ward_id_col, population_col, *columns.values()]
    missing_columns = [c for c in required if c not in wards.columns]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if wards[ward_id_col].isna().any():
        raise ValueError("Ward identifiers cannot be missing.")

    if wards[ward_id_col].duplicated().any():
        raise ValueError("Ward identifiers must be unique.")

    result = wards.copy()

    # Validate known values without replacing missing values with zero.
    for column in [population_col, *columns.values()]:
        for value in result[column].dropna():
            if not _valid_number(value):
                raise ValueError(
                    f"{column} must contain non-negative finite numbers."
                )

    population_complete = result[population_col].notna().all()

    city_population = (
        float(result[population_col].sum())
        if population_complete
        else np.nan
    )

    population_total_valid = (
        population_complete and city_population > 0
    )

    result["population_total_valid"] = population_total_valid
    result["priority_data_complete"] = True
    result["data_quality_notes"] = ""

    if not population_complete:
        result["priority_data_complete"] = False
        result["data_quality_notes"] = (
            "Population is missing in one or more wards."
        )
    elif city_population <= 0:
        result["priority_data_complete"] = False
        result["data_quality_notes"] = (
            "Citywide population must be greater than zero."
        )

    category_scores = []

    for category, count_col in columns.items():
        expected_col = f"{category}_expected"
        rate_col = f"{category}_per_10000"
        score_col = f"{category}_priority_score"
        shortfall_col = f"{category}_shortfall"

        counts_complete = result[count_col].notna().all()
        benchmark_available = population_total_valid and counts_complete

        result[expected_col] = np.nan
        result[rate_col] = np.nan
        result[score_col] = np.nan
        result[shortfall_col] = np.nan

        if not counts_complete:
            result["priority_data_complete"] = False
            result["data_quality_notes"] = result[
                "data_quality_notes"
            ].apply(
                lambda note: (
                    f"{note}; " if note else ""
                ) + f"{category}: facility counts are incomplete."
            )
            category_scores.append(score_col)
            continue

        result[rate_col] = result.apply(
            lambda row: facilities_per_10000(
                float(row[count_col]),
                float(row[population_col]),
            ) if _valid_number(row[population_col]) else np.nan,
            axis=1,
        )

        if not benchmark_available:
            category_scores.append(score_col)
            continue

        city_facility_total = float(result[count_col].sum())

        if city_facility_total == 0:
            result["priority_data_complete"] = False
            result["data_quality_notes"] = result[
                "data_quality_notes"
            ].apply(
                lambda note: (
                    f"{note}; " if note else ""
                ) + f"{category}: no mapped facilities to benchmark."
            )
            category_scores.append(score_col)
            continue

        result[expected_col] = result[population_col].apply(
            lambda population: expected_facilities(
                city_facility_total,
                float(population),
                city_population,
            )
        )

        result[shortfall_col] = (
            result[expected_col] - result[count_col]
        ).clip(lower=0)

        result[score_col] = (
            result[shortfall_col] / result[expected_col] * 100
        ).where(result[expected_col] > 0, np.nan)

        category_scores.append(score_col)

    # Weights apply only to available category scores.
    # Category-specific scores never depend on unrelated categories.
    configured_weights = dict(weights or {})
    unknown_weights = set(configured_weights) - set(categories)

    if unknown_weights:
        raise ValueError(
            f"Weights contain unknown categories: {sorted(unknown_weights)}"
        )

    for category in categories:
        weight = configured_weights.get(category, 1.0)
        if not np.isfinite(weight) or weight < 0:
            raise ValueError("Weights must be finite and non-negative.")

    result["overall_priority_score"] = np.nan

    weight_total = sum(
        configured_weights.get(category, 1.0)
        for category in categories
    )

    if weight_total > 0:
        for index, row in result.iterrows():
            available = [
                category
                for category in categories
                if pd.notna(row[f"{category}_priority_score"])
                and configured_weights.get(category, 1.0) > 0
            ]

            available_weight = sum(
                configured_weights.get(category, 1.0)
                for category in available
            )

            if available_weight > 0:
                result.loc[index, "overall_priority_score"] = sum(
                    row[f"{category}_priority_score"]
                    * configured_weights.get(category, 1.0)
                    for category in available
                ) / available_weight

    return result
