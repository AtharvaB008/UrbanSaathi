"""
UrbanSaathi — Complaint Intelligence

Detects potentially related civic complaints
and supports evidence-based investigation
priority recommendations.

This module does not automatically modify
complaint statuses or database records.
"""

from difflib import SequenceMatcher

def normalize_complaint_text(text):
    """Normalize complaint text for similarity comparison."""

    if not text:
        return ""

    return " ".join(str(text).lower().split())

    from difflib import SequenceMatcher


def calculate_complaint_similarity(complaint_a, complaint_b):
    """
    Estimate whether two complaints describe the same issue.

    Combines textual similarity with locality information.
    This is a heuristic score, not a probability.
    """

    if complaint_a["ward_id"] != complaint_b["ward_id"]:
        return 0.0

    if complaint_a["category"] != complaint_b["category"]:
        return 0.0

    def complaint_text(complaint):
        return normalize_complaint_text(
            " ".join([
                str(complaint.get("title") or ""),
                str(complaint.get("description") or ""),
            ])
        )

    text_a = complaint_text(complaint_a)
    text_b = complaint_text(complaint_b)

    if not text_a or not text_b:
        return 0.0

    text_score = SequenceMatcher(
        None, text_a, text_b
    ).ratio()

    locality_a = normalize_complaint_text(
        complaint_a.get("locality")
    )
    locality_b = normalize_complaint_text(
        complaint_b.get("locality")
    )

    if locality_a and locality_b:
        locality_score = SequenceMatcher(
            None, locality_a, locality_b
        ).ratio()

        if locality_score < 0.5:
            return round(text_score * 0.4, 3)

        combined_score = (
            0.70 * text_score
            + 0.30 * locality_score
        )
    else:
        combined_score = text_score

    # Compare nearby landmarks when both reports contain them.
    landmark_a = normalize_complaint_text(
        complaint_a.get("location_details")
    )
    landmark_b = normalize_complaint_text(
        complaint_b.get("location_details")
    )

    if landmark_a and landmark_b:
        landmark_score = SequenceMatcher(
            None, landmark_a, landmark_b
        ).ratio()

        if landmark_score < 0.5:
            return round(combined_score * 0.4, 3)

        combined_score = (
            0.80 * combined_score
            + 0.20 * landmark_score
        )

    return round(combined_score, 3)




def find_potential_duplicates(
    complaints,
    similarity_threshold=0.65
):
    """
    Find pairs of potentially duplicate complaints.

    Does not change complaint records or statuses.
    """

    matches = []

    for i in range(len(complaints)):
        for j in range(i + 1, len(complaints)):

            complaint_a = complaints[i]
            complaint_b = complaints[j]

            similarity = calculate_complaint_similarity(
                complaint_a,
                complaint_b
            )

            if similarity >= similarity_threshold:
                matches.append({
                    "report_id_1": complaint_a["report_id"],
                    "report_id_2": complaint_b["report_id"],
                    "similarity_score": round(similarity, 3),
                    "ward_id": complaint_a["ward_id"],
                    "category": complaint_a["category"],
                })

    return sorted(
        matches,
        key=lambda match: match["similarity_score"],
        reverse=True
    )

def get_live_potential_duplicates(similarity_threshold=0.65):
    """
    Retrieve potentially duplicate complaints from SQLite.

    Only active complaints are compared.
    This function does not change database records.
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

    return find_potential_duplicates(
        active_reports,
        similarity_threshold=similarity_threshold,
    )