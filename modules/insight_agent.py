import pandas as pd

"""
UrbanSaathi — Municipal Insight Agent

Explains existing ward priority scores, facility benchmarks,
missing data, and summaries of civic reports.
"""


def explain_ward(ward):
    """Explain the supplied ward data without recalculating its score."""
    ward_id = ward.get("ward_id", "Unknown")
    ward_name = ward.get("ward_name", ward_id)

    priority = ward.get("priority") or {}
    score = priority.get("score")

    facilities = ward.get("facilities") or {}
    missing_data = ward.get("missing_data") or []

    warnings = []
    investigations = []
    facility_findings = []

    # Explain the existing priority score.
    if score is None:
        summary = f"No priority score is available for {ward_name}."
        warnings.append("Official priority score is unavailable.")
    else:
        summary = f"{ward_name} has a priority score of {score}."

    # Explain facility counts and benchmarks separately.
    for category, details in facilities.items():
        details = details or {}
        actual = details.get("actual_count")
        benchmark = details.get("benchmark_count")

        if actual is None:
            status = "insufficient_data"
            shortfall = None
            warnings.append(
                f"{category}: facility count is unavailable."
            )
            investigations.append(
                f"Check the mapped facility records for {category}."
            )

        elif benchmark is None:
            status = "benchmark_unavailable"
            shortfall = None

        else:
            shortfall = max(benchmark - actual, 0)

            if actual < benchmark:
                status = "below_benchmark"
                investigations.append(
                    f"Investigate the {category} facility shortfall "
                    f"of {shortfall}."
                )
            elif actual == benchmark:
                status = "at_benchmark"
            else:
                status = "above_benchmark"

        facility_findings.append({
            "category": category,
            "status": status,
            "actual_count": actual,
            "benchmark_count": benchmark,
            "shortfall": shortfall,
            "source": details.get("source"),
        })

    # Coverage is supplied as a percentage, from 0 to 100.
    coverage = ward.get("coverage")

    if coverage is not None and coverage < 100:
        warnings.append(
            f"Data coverage is {coverage}%; interpret this assessment "
            "cautiously because some information may be missing."
        )

    # Include only the missing-data descriptions supplied by the dataset.
    for item in missing_data:
        warnings.append(f"Missing data: {item}")
        investigations.append(f"Investigate missing data: {item}")

    component_findings = priority.get("components") or []

    return {
        "ward_id": ward_id,
        "ward_name": ward_name,
        "priority_score": score,
        "summary": summary,
        "facility_findings": facility_findings,
        "component_findings": component_findings,
        "warnings": warnings,
        "investigations": investigations,
        "coverage": coverage,
        "population": ward.get("population"),
        "population_density": ward.get("population_density"),
        "disclaimer": (
            "Facility benchmarks are comparison references, not proof of "
            "service quality, capacity, accessibility, or actual community "
            "need. The agent explains supplied scores and does not calculate "
            "or replace the official priority score."
        ),
    }


def compare_wards(ward_a, ward_b):
    """Compare two wards using their existing priority scores."""
    first = explain_ward(ward_a)
    second = explain_ward(ward_b)

    score_a = first["priority_score"]
    score_b = second["priority_score"]

    if score_a is not None and score_b is not None:
        difference = score_a - score_b

        if difference > 0:
            relation = "higher"
        elif difference < 0:
            relation = "lower"
        else:
            relation = "equal"

        comparison = (
            f"{first['ward_name']} has a score of {score_a}, while "
            f"{second['ward_name']} has a score of {score_b}. "
            f"The first ward's score is {abs(difference)} points "
            f"{relation}."
        )
    else:
        difference = None
        comparison = (
            "An official score comparison is unavailable because "
            "one or both wards do not have a priority score."
        )

    return {
        "ward_a": first,
        "ward_b": second,
        "score_difference_a_minus_b": difference,
        "score_comparison": comparison,
    }


def summarize_reports(
    reports,
    ward_id=None,
    period_label="provided reporting period",
):
    """Summarize supplied civic reports without inventing records."""
    from collections import Counter

    filtered = [
        report for report in reports
        if ward_id is None or str(report.get("ward_id")) == str(ward_id)
    ]

    categories = Counter(
        report.get("category", "Uncategorized")
        for report in filtered
    )
    statuses = Counter(
        report.get("status", "Unknown")
        for report in filtered
    )
    wards = Counter(
        report.get("ward_id", "Unknown")
        for report in filtered
    )

    return {
        "ward_id": ward_id,
        "period": period_label,
        "total_reports": len(filtered),
        "category_counts": dict(categories),
        "status_counts": dict(statuses),
        "ward_counts": dict(wards),
        "recurring_categories": [
            category
            for category, count in categories.items()
            if count >= 2
        ],
    }


def generate_diagnostics_insights(
    wards,
    category_columns,
    score_columns,
    top_n=5,
):
    """
    Generate evidence-based municipal investigation suggestions from
    the facility counts and gap scores already calculated by diagnostics.py.

    This function does not recalculate or change the official page scores.
    """
    if wards is None or wards.empty:
        return {
            "summary": "No ward data is available for analysis.",
            "priority_wards": [],
            "recommendations": [],
        }

    data = wards.copy()
    score_column = "Overall Priority Score"

    if score_column not in data.columns:
        return {
            "summary": "The overall priority score is unavailable.",
            "priority_wards": [],
            "recommendations": [],
        }

    data[score_column] = pd.to_numeric(
        data[score_column], errors="coerce"
    )

    ranked = data.dropna(subset=[score_column]).sort_values(
        [score_column, "KGISWardNo"],
        ascending=[False, True],
    )

    if ranked.empty:
        return {
            "summary": (
                "Overall scores cannot be compared because valid scores "
                "are unavailable."
            ),
            "priority_wards": [],
            "recommendations": [],
        }

    highest = ranked.iloc[0]
    highest_ward = highest["KGISWardNo"]
    highest_score = float(highest[score_column])

    priority_wards = []
    recommendations = []

    for _, ward in ranked.head(top_n).iterrows():
        ward_no = ward["KGISWardNo"]
        overall_score = float(ward[score_column])

        priority_wards.append({
            "ward": ward_no,
            "score": round(overall_score, 1),
        })

        for category, count_column in category_columns.items():
            category_score_column = score_columns.get(category)

            if (
                count_column not in data.columns
                or category_score_column not in data.columns
            ):
                continue

            count = ward[count_column]
            gap_score = ward[category_score_column]

            if pd.isna(count) or pd.isna(gap_score):
                continue

            count = int(count)
            gap_score = float(gap_score)

            if gap_score <= 0:
                continue

            if count == 0:
                evidence = (
                    f"Ward {ward_no} has no mapped {category.lower()} "
                    "facilities, while the citywide total is non-zero."
                )
                action = (
                    f"Prioritise a ground survey in Ward {ward_no} to "
                    f"check whether {category.lower()} facilities are "
                    "missing from the map, located outside the ward, "
                    "or genuinely absent. Assess nearby alternatives "
                    "before considering new provision."
                )
                urgency = "Investigate first"
            else:
                evidence = (
                    f"Ward {ward_no} has {count} mapped "
                    f"{category.lower()} facilities and a "
                    f"{gap_score:.1f}/100 relative distribution gap score."
                )
                action = (
                    f"Review the location and service coverage of the "
                    f"{count} mapped {category.lower()} facilities in "
                    f"Ward {ward_no}. Compare resident demand, travel "
                    "times, operating status and facility capacity with "
                    "nearby wards before deciding whether to improve "
                    "access or expand provision."
                )
                urgency = (
                    "High investigation priority"
                    if gap_score >= 50
                    else "Further assessment"
                )

            recommendations.append({
                "ward": ward_no,
                "category": category,
                "gap_score": round(gap_score, 1),
                "facility_count": count,
                "urgency": urgency,
                "evidence": evidence,
                "action": action,
            })

    recommendations.sort(
        key=lambda item: (
            -item["gap_score"],
            float(item["ward"]),
            item["category"],
        )
    )

    return {
        "summary": (
            f"Ward {highest_ward} has the highest overall relative "
            f"distribution gap score ({highest_score:.1f}/100) among "
            f"wards with available scores. This identifies where to "
            "investigate first, not where a new facility is automatically "
            "required."
        ),
        "priority_wards": priority_wards,
        "recommendations": recommendations,
    }
