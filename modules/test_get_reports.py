
from report_service import submit_report, get_reports
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.init_db import get_connection


report_id = None

try:
    # Create a temporary complaint.
    report_id = submit_report(
        title="TEST - Water supply issue",
        category="Water",
        description="Water supply is interrupted.",
        ward_id=12,
        locality="Test locality",
        location_details="Near the test community hall"
    )

    print("Test report created:", report_id)

    # Retrieve all reports.
    all_reports = get_reports()
    assert any(
        r["report_id"] == report_id for r in all_reports
    )
    print("PASS: Report appears in all reports.")

    # Filter by category.
    water_reports = get_reports(category="Water")
    assert any(
        r["report_id"] == report_id for r in water_reports
    )
    print("PASS: Category filter works.")

    # Filter by ward.
    ward_reports = get_reports(ward_id=12)
    assert any(
        r["report_id"] == report_id for r in ward_reports
    )
    print("PASS: Ward filter works.")

    # Filter by status.
    submitted_reports = get_reports(status="Submitted")
    assert any(
        r["report_id"] == report_id for r in submitted_reports
    )
    print("PASS: Status filter works.")

    # Check a filter that should exclude this report.
    other_ward_reports = get_reports(ward_id=13)
    assert not any(
        r["report_id"] == report_id for r in other_ward_reports
    )
    print("PASS: Other ward correctly excludes report.")

    # Check combined filters.
    combined = get_reports(
        category="Water",
        ward_id=12,
        status="Submitted"
    )
    assert any(
        r["report_id"] == report_id for r in combined
    )
    print("PASS: Combined filters work.")

    print("All report retrieval tests passed!")

finally:
    # Clean up even if a test fails.
    if report_id is not None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM civic_reports WHERE report_id = ?",
                (report_id,)
            )
        print("Temporary test report removed.")
