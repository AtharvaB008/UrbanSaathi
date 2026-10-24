from datetime import datetime, timezone

from modules.investigation_priority import (
    calculate_investigation_priority,
    calculate_all_complaint_priorities,
    classify_investigation_priority,
)


# Fixed time makes the tests reproducible.
NOW = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


def make_complaint(report_id, category, created_at):
    return {
        "report_id": report_id,
        "category": category,
        "created_at": created_at,
    }


print("Testing investigation priority classification...")

assert classify_investigation_priority(20) == "Low"
assert classify_investigation_priority(40) == "Medium"
assert classify_investigation_priority(70) == "High"

print("Priority classification passed!")


print("\nTesting low-priority complaint...")

low_complaint = make_complaint(
    401,
    "Other civic issue",
    "2026-10-25T08:00:00+00:00",
)

low_result = calculate_investigation_priority(
    low_complaint,
    related_complaint_count=0,
    current_time=NOW,
)

print(low_result)

assert low_result["priority_score"] == 15
assert low_result["priority_level"] == "Low"


print("\nTesting medium-priority complaint...")

medium_complaint = make_complaint(
    402,
    "Water",
    "2026-10-20T12:00:00+00:00",
)

medium_result = calculate_investigation_priority(
    medium_complaint,
    related_complaint_count=1,
    current_time=NOW,
)

print(medium_result)

assert medium_result["priority_score"] == 50
assert medium_result["priority_level"] == "Medium"


print("\nTesting high-priority complaint...")

high_complaint = make_complaint(
    403,
    "Drainage & waterlogging",
    "2026-10-17T12:00:00+00:00",
)

high_result = calculate_investigation_priority(
    high_complaint,
    related_complaint_count=3,
    current_time=NOW,
)

print(high_result)

assert high_result["priority_score"] == 85
assert high_result["priority_level"] == "High"


print("\nTesting duplicate-score limit...")

capped_result = calculate_investigation_priority(
    high_complaint,
    related_complaint_count=20,
    current_time=NOW,
)

assert capped_result["duplicate_score"] == 35
assert capped_result["priority_score"] <= 100

print("Duplicate-score limit passed!")

print("\nTesting automatic duplicate counting and priorities...")

sample_reports = [
    {
        "report_id": 501,
        "ward_id": 15,
        "category": "Drainage & waterlogging",
        "title": "Blocked drain near market",
        "description": "Blocked drain near the market entrance.",
        "locality": "Central Market",
        "location_details": "Main market entrance",
        "created_at": "2026-10-17T12:00:00+00:00",
    },
    {
        "report_id": 502,
        "ward_id": 15,
        "category": "Drainage & waterlogging",
        "title": "Blocked drain near market",
        "description": "Blocked drain near the market entrance.",
        "locality": "Central Market",
        "location_details": "Main market entrance",
        "created_at": "2026-10-17T12:00:00+00:00",
    },
    {
        "report_id": 503,
        "ward_id": 15,
        "category": "Drainage & waterlogging",
        "title": "Blocked drain near market",
        "description": "Blocked drain near the market entrance.",
        "locality": "Central Market",
        "location_details": "Main market entrance",
        "created_at": "2026-10-17T12:00:00+00:00",
    },
    {
        "report_id": 504,
        "ward_id": 18,
        "category": "Other civic issue",
        "title": "Damaged public bench",
        "description": "A park bench requires repair.",
        "locality": "City Park",
        "location_details": "Near the park gate",
        "created_at": "2026-10-25T08:00:00+00:00",
    },
]

recommendations = calculate_all_complaint_priorities(
    sample_reports,
    current_time=NOW,
)

for recommendation in recommendations:
    print(
        "Report:",
        recommendation["report_id"],
        "| Related:",
        recommendation["related_complaint_count"],
        "| Score:",
        recommendation["priority_score"],
        "| Priority:",
        recommendation["priority_level"],
    )

results_by_id = {
    item["report_id"]: item
    for item in recommendations
}

for report_id in (501, 502, 503):
    assert results_by_id[report_id]["related_complaint_count"] == 2
    assert results_by_id[report_id]["priority_score"] == 75
    assert results_by_id[report_id]["priority_level"] == "High"

assert results_by_id[504]["related_complaint_count"] == 0
assert results_by_id[504]["priority_score"] == 15
assert results_by_id[504]["priority_level"] == "Low"

assert recommendations[0]["priority_score"] == 75
assert recommendations[-1]["report_id"] == 504

print("Automatic duplicate counting and priority tests passed!")

print("\nSUCCESS: All investigation priority tests passed!")