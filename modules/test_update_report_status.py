
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.init_db import get_connection
from modules.report_service import submit_report, update_report_status, get_report_by_id

report_id = None

try:
    # Create a temporary complaint.
    report_id = submit_report(
        title="TEST - Broken streetlight",
        category="Electricity / street lighting",
        description="A streetlight is not working near the park.",
        ward_id=12,
        locality="Test locality",
        location_details="Near the public park"
    )

    print("Test report created:", report_id)

    # Change its status.
    result = update_report_status(
        report_id,
        "Under Review",
        "Administrator is checking the complaint."
    )

    assert result is True

    # Check the updated report.
    report = get_report_by_id(report_id)

    assert report["status"] == "Under Review"
    print("PASS: Status changed to Under Review.")

    # Check the status history.
    with get_connection() as connection:
        history = connection.execute(
            """
            SELECT old_status, new_status, admin_note
            FROM report_status_history
            WHERE report_id = ?
            ORDER BY history_id
            """,
            (report_id,)
        ).fetchall()

    assert len(history) == 2
    assert history[1]["old_status"] == "Submitted"
    assert history[1]["new_status"] == "Under Review"
    assert history[1]["admin_note"] == "Administrator is checking the complaint."

    print("PASS: Status history recorded correctly.")

    # Rejection without a reason must fail.
    try:
        update_report_status(report_id, "Rejected / Invalid")
        raise AssertionError("Rejection without a reason was accepted!")
    except ValueError as error:
        assert "reason" in str(error).lower()

    print("PASS: Rejection without a reason was blocked.")

    # Rejection with a reason should succeed.
    update_report_status(
        report_id,
        "Rejected / Invalid",
        "Duplicate complaint."
    )

    report = get_report_by_id(report_id)
    assert report["status"] == "Rejected / Invalid"

    print("PASS: Rejection with a reason succeeded.")
    print("All status-update tests passed!")

finally:
    # Remove the temporary test report.
    if report_id is not None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM civic_reports WHERE report_id = ?",
                (report_id,)
            )

        print("Temporary test report removed.")
