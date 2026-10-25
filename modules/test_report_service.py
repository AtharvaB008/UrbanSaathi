
from report_service import submit_report
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.init_db import get_connection


# Submit a sample complaint.
report_id = submit_report(
    title="TEST - Broken streetlight",
    category="Electricity / street lighting",
    description="Streetlight near the bus stop is not working.",
    ward_id=12,
    locality="Test locality",
    location_details="Near the main bus stop"
)

print("Report submitted successfully!")
print("Report ID:", report_id)

# Verify the complaint and its status history.
with get_connection() as connection:
    report = connection.execute(
        "SELECT * FROM civic_reports WHERE report_id = ?",
        (report_id,)
    ).fetchone()

    history = connection.execute(
        """
        SELECT * FROM report_status_history
        WHERE report_id = ?
        """,
        (report_id,)
    ).fetchall()

    assert report is not None, "Report was not saved."
    assert report["status"] == "Submitted"
    assert len(history) == 1, "Initial status history is missing."
    assert history[0]["new_status"] == "Submitted"

    print("Saved title:", report["title"])
    print("Saved status:", report["status"])
    print("History records:", len(history))

    # Remove only the sample report created by this test.
    connection.execute(
        "DELETE FROM civic_reports WHERE report_id = ?",
        (report_id,)
    )

print("Test complaint removed.")
print("All complaint submission tests passed!")
