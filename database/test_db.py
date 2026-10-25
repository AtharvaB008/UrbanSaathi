
from init_db import get_connection, init_database

# Ensure the database exists
init_database()

with get_connection() as connection:
    # Read a ward
    ward = connection.execute(
        "SELECT ward_id, ward_name FROM wards WHERE ward_id = ?",
        (12,)
    ).fetchone()

    print("Ward found:", dict(ward))

    # Insert a temporary civic report
    cursor = connection.execute(
        """
        INSERT INTO civic_reports (
            title, category, description,
            ward_id, locality, location_details
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "TEST - Broken streetlight",
            "Electricity / street lighting",
            "Temporary test complaint",
            12,
            "Test locality",
            "Near test bus stop"
        )
    )

    report_id = cursor.lastrowid
    print("Test report inserted:", report_id)

    # Read the inserted report
    report = connection.execute(
        "SELECT * FROM civic_reports WHERE report_id = ?",
        (report_id,)
    ).fetchone()

    print("Report found:", report["title"])
    print("Report status:", report["status"])

    # Remove the temporary report
    connection.execute(
        "DELETE FROM civic_reports WHERE report_id = ?",
        (report_id,)
    )

    print("Temporary test report removed.")

print("Database insert/read test completed successfully!")
