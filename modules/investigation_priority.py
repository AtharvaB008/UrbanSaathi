"""
UrbanSaathi — Complaint Investigation Priority

Provides advisory investigation priorities based on
available civic complaint evidence.

Recommendations do not automatically change
complaint statuses or administrative decisions.
"""

from datetime import datetime, timezone
from modules.complaint_intelligence import find_potential_duplicates

def classify_investigation_priority(score):
    """Convert a numerical score into a priority label."""

    if score >= 70:
        return "High"

    if score >= 40:
        return "Medium"

    return "Low"

    from datetime import datetime, timezone


CATEGORY_SCORES = {
    "Water": 30,
    "Electricity / street lighting": 30,
    "Roads & public property": 25,
    "Waste & sanitation": 25,
    "Drainage & waterlogging": 40,
    "Other civic issue": 15,
}


def calculate_investigation_priority(
    complaint,
    related_complaint_count=0,
    current_time=None,
):
    """
    Calculate an advisory investigation priority.

    related_complaint_count counts other potentially
    related reports, excluding the current complaint.
    """

    category = complaint.get("category", "Other civic issue")
    category_score = CATEGORY_SCORES.get(category, 15)

    related_count = max(0, int(related_complaint_count))

    # Each additional related complaint contributes 10 points.
    # The contribution is capped at 35 points.
    duplicate_score = min(related_count * 10, 35)

    age_score = 0
    created_at = complaint.get("created_at")

    if created_at:
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(
                created_at.replace("Z", "+00:00")
            )

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        age_days = max(
            0,
            (current_time - created_at).total_seconds() / 86400,
        )

        if age_days >= 14:
            age_score = 25
        elif age_days >= 7:
            age_score = 15
        elif age_days >= 3:
            age_score = 10

    total_score = category_score + duplicate_score + age_score
    total_score = min(total_score, 100)

    return {
        "report_id": complaint.get("report_id"),
        "priority_score": total_score,
        "priority_level": classify_investigation_priority(
            total_score
        ),
        "category_score": category_score,
        "duplicate_score": duplicate_score,
        "age_score": age_score,
        "related_complaint_count": related_count,
    }

def calculate_all_complaint_priorities(
    complaints,
    similarity_threshold=0.65,
    current_time=None,
):
    """
    Calculate investigation priorities for multiple complaints.

    Automatically counts potentially related reports.
    Does not modify SQLite records or complaint statuses.
    """

    complaints = list(complaints)

    duplicate_matches = find_potential_duplicates(
        complaints,
        similarity_threshold=similarity_threshold,
    )

    related_counts = {
        complaint["report_id"]: 0
        for complaint in complaints
    }

    for match in duplicate_matches:
        report_a = match["report_id_1"]
        report_b = match["report_id_2"]

        related_counts[report_a] += 1
        related_counts[report_b] += 1

    recommendations = []

    for complaint in complaints:
        report_id = complaint["report_id"]

        result = calculate_investigation_priority(
            complaint,
            related_complaint_count=related_counts[report_id],
            current_time=current_time,
        )

        recommendations.append(result)

    return sorted(
        recommendations,
        key=lambda item: (
            -item["priority_score"],
            item["report_id"],
        ),
    )

def get_live_investigation_recommendations(
    similarity_threshold=0.65,
    current_time=None,
):
    """
    Generate investigation recommendations from SQLite.

    Only active complaints are considered.
    This function does not modify the database.
    """

    from modules.report_service import get_reports

    all_reports = get_reports()

    closed_statuses = {
        "Resolved",
        "Rejected / Invalid",
    }

    active_reports = [
        report
        for report in all_reports
        if report["status"] not in closed_statuses
    ]

    recommendations = calculate_all_complaint_priorities(
        active_reports,
        similarity_threshold=similarity_threshold,
        current_time=current_time,
    )

    return recommendations

def explain_investigation_priority(recommendation):
    """
    Generate an evidence-based explanation
    for a complaint's recommended priority.
    """

    category_score = recommendation["category_score"]
    duplicate_score = recommendation["duplicate_score"]
    age_score = recommendation["age_score"]
    related_count = recommendation["related_complaint_count"]

    explanation = (
        f"This complaint received a "
        f"{recommendation['priority_level']} investigation "
        f"priority recommendation with a score of "
        f"{recommendation['priority_score']}/100. "
        f"The score includes {category_score} points "
        f"for the complaint category, "
        f"{duplicate_score} points for potentially "
        f"related complaints, and {age_score} points "
        f"for complaint age. "
    )

    if related_count == 0:
        explanation += (
            "No potentially related active complaints "
            "were detected by the current similarity rules."
        )
    else:
        explanation += (
            f"The system identified {related_count} "
            f"potentially related active complaint(s). "
            "These matches require administrator verification."
        )

    return explanation