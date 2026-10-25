
from report_service import submit_report, get_report_by_id
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.init_db import get_connection


report_id = None

try:
    # Create a temporary complaint.
    report_id = submit_report(
        title="TEST - Damaged road",
        category="Roads & public property",
        description="A road near the market needs repair.",
        ward_id=12,
        locality="Test locality",
        location_details="Near the main market"
    )

    print("Test report created:", report_id)

    # Retrieve the complaint using its ID.
    report = get_report_by_id(report_id)

    assert report is not None
    assert report["report_id"] == report_id
    assert report["title"] == "TEST - Damaged road"
    assert report["ward_id"] == 12
    assert report["status"] == "Submitted"

    print("PASS: Report retrieved successfully.")
    print("Title:", report["title"])
    print("Ward:", report["ward_id"])
    print("Status:", report["status"])

    # Check a report ID that does not exist.
    missing_report = get_report_by_id(999999)
    assert missing_report is None

    print("PASS: Missing report handled correctly.")
    print("All single-report retrieval tests passed!")

finally:
    # Remove the temporary complaint.
    if report_id is not None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM civic_reports WHERE report_id = ?",
                (report_id,)
            )

        print("Temporary test report removed.")
