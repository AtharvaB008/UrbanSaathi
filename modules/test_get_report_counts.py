
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.init_db import get_connection
from modules.report_service import (
    submit_report,
    update_report_status,
    get_report_counts,
)

created_report_ids = []

try:
    # Record the existing counts so the test also works
    # if other complaints are already in the database.
    before_all = get_report_counts()
    before_ward_12 = get_report_counts(ward_id=12)
    before_ward_13 = get_report_counts(ward_id=13)

    # Create the first temporary complaint in Ward 12.
    report_1 = submit_report(
        title="TEST - Streetlight issue",
        category="Electricity / street lighting",
        description="A streetlight is not working.",
        ward_id=12,
        locality="Test locality",
        location_details="Near the park",
    )
    created_report_ids.append(report_1)

    # Create a second complaint in Ward 12.
    report_2 = submit_report(
        title="TEST - Water issue",
        category="Water",
        description="Water supply is interrupted.",
        ward_id=12,
        locality="Test locality",
        location_details="Near the market",
    )
    created_report_ids.append(report_2)

    # Create a third complaint in Ward 13.
    report_3 = submit_report(
        title="TEST - Road issue",
        category="Roads & public property",
        description="A road needs repair.",
        ward_id=13,
        locality="Test locality",
        location_details="Near the bus stop",
    )
    created_report_ids.append(report_3)

    print("Three temporary reports created.")

    # Change the status of two complaints.
    update_report_status(
        report_2,
        "Under Review",
        "Complaint being checked.",
    )

    update_report_status(
        report_3,
        "Resolved",
        "Issue addressed.",
    )

    # Check citywide counts.
    after_all = get_report_counts()

    assert after_all["Total"] == before_all["Total"] + 3
    assert after_all["Submitted"] == before_all["Submitted"] + 1
    assert after_all["Under Review"] == before_all["Under Review"] + 1
    assert after_all["Resolved"] == before_all["Resolved"] + 1

    print("PASS: Citywide complaint counts are correct.")

    # Check Ward 12 counts.
    after_ward_12 = get_report_counts(ward_id=12)

    assert after_ward_12["Total"] == before_ward_12["Total"] + 2
    assert (
        after_ward_12["Submitted"]
        == before_ward_12["Submitted"] + 1
    )
    assert (
        after_ward_12["Under Review"]
        == before_ward_12["Under Review"] + 1
    )

    print("PASS: Ward 12 complaint counts are correct.")

    # Check Ward 13 counts.
    after_ward_13 = get_report_counts(ward_id=13)

    assert after_ward_13["Total"] == before_ward_13["Total"] + 1
    assert (
        after_ward_13["Resolved"]
        == before_ward_13["Resolved"] + 1
    )

    print("PASS: Ward 13 complaint counts are correct.")

    # Check that every status is included in the result.
    expected_keys = {
        "Submitted",
        "Under Review",
        "In Progress",
        "Resolved",
        "Rejected / Invalid",
        "Total",
    }

    assert set(after_all.keys()) == expected_keys
    print("PASS: All five statuses and total are included.")

    # Invalid ward IDs must be rejected.
    try:
        get_report_counts(ward_id=61)
        raise AssertionError("Invalid ward ID was accepted!")
    except ValueError:
        print("PASS: Invalid ward ID was rejected.")

    print("All complaint-count tests passed!")

finally:
    # Remove the temporary reports and their status history.
    with get_connection() as connection:
        for report_id in created_report_ids:
            connection.execute(
                "DELETE FROM civic_reports WHERE report_id = ?",
                (report_id,),
            )

    print("Temporary test reports removed.")
