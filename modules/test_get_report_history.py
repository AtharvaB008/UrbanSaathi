
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.init_db import get_connection
from modules.report_service import (
    submit_report,
    update_report_status,
    get_report_history,
)

report_id = None

try:
    # Create a temporary complaint.
    report_id = submit_report(
        title="TEST - Water supply issue",
        category="Water",
        description="Water supply is interrupted in this locality.",
        ward_id=12,
        locality="Test locality",
        location_details="Near the main road",
    )

    print("Test report created:", report_id)

    # Record two administrative status changes.
    update_report_status(
        report_id,
        "Under Review",
        "Checking the water supply complaint.",
    )

    update_report_status(
        report_id,
        "In Progress",
        "The issue has been confirmed and action is underway.",
    )

    # Retrieve the full status history.
    history = get_report_history(report_id)

    assert len(history) == 3
    print("PASS: Three history entries retrieved.")

    assert history[0]["new_status"] == "Submitted"
    assert history[1]["new_status"] == "Under Review"
    assert history[2]["new_status"] == "In Progress"
    print("PASS: Status changes are in the correct order.")

    assert history[1]["old_status"] == "Submitted"
    assert history[2]["old_status"] == "Under Review"
    print("PASS: Previous statuses recorded correctly.")

    assert history[1]["admin_note"] == (
        "Checking the water supply complaint."
    )
    assert history[2]["admin_note"] == (
        "The issue has been confirmed and action is underway."
    )
    print("PASS: Administrator notes retrieved correctly.")

    assert all(entry["changed_at"] for entry in history)
    print("PASS: Timestamps are present.")

    missing_history = get_report_history(999999)
    assert missing_history == []
    print("PASS: Nonexistent report returns an empty history.")

    print("All report-history tests passed!")

finally:
    # Delete the temporary complaint.
    # Its history entries are deleted automatically
    # because of the database's ON DELETE CASCADE rule.
    if report_id is not None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM civic_reports WHERE report_id = ?",
                (report_id,),
            )

        print("Temporary test report removed.")
