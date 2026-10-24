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
        warnings.append("Priority score is missing.")
        investigations.append(
            "Investigate why the priority score is unavailable."
        )
    else:
        summary = f"{ward_name} has a priority score of {score}."

    # Explain each facility category against its benchmark.
    for category, details in facilities.items():
        details = details or {}
        actual = details.get("actual_count")
        benchmark = details.get("benchmark_count")

        if actual is None or benchmark is None:
            status = "insufficient_data"
            shortfall = None
            warnings.append(
                f"{category}: facility count or benchmark is unavailable."
            )
            investigations.append(
                f"Verify the facility data and benchmark for {category}."
            )
        else:
            shortfall = max(benchmark - actual, 0)

            if actual < benchmark:
                status = "below_benchmark"
                investigations.append(
                    f"Investigate the {category} facility shortfall of "
                    f"{shortfall}."
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

    # Include the specific missing-data descriptions supplied by the dataset.
    for item in missing_data:
        warnings.append(f"Missing data: {item}")
        investigations.append(f"Investigate missing data: {item}")

    # Explain priority-score components.
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
        comparison = (
            f"{first['ward_name']} has a score of {score_a}, while "
            f"{second['ward_name']} has a score of {score_b}. "
            f"The first ward's score is {abs(difference)} points "
            f"{'higher' if difference > 0 else 'lower' if difference < 0 else 'equal'}."
        )
    else:
        difference = None
        comparison = (
            "A score comparison is unavailable because one or both "
            "wards do not have a priority score."
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
        if ward_id is None or report.get("ward_id") == ward_id
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