
from pathlib import Path
import sys
import math

# Allow direct execution from the project repository.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.init_db import get_connection


REPORT_CATEGORIES = (
    "Water",
    "Electricity / street lighting",
    "Roads & public property",
    "Waste & sanitation",
    "Drainage & waterlogging",
    "Other civic issue",
)


def submit_report(
    title,
    category,
    description,
    ward_id,
    locality,
    location_details,
        latitude=None,
    longitude=None,
    photo_path=None,
    resident_id=None,
):
    """Validate and save a civic report with its initial history."""

    # Validate mandatory text fields.
    fields = {
        "Title": title,
        "Description": description,
        "Locality": locality,
        "Location details": location_details,
    }

    for field_name, value in fields.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required.")

    if category not in REPORT_CATEGORIES:
        raise ValueError("Invalid civic report category.")

    # Validate ward number.
    if isinstance(ward_id, bool):
        raise ValueError("Ward must be a number from 1 to 60.")

    try:
        ward_number = int(ward_id)
    except (ValueError, TypeError, OverflowError):
        raise ValueError("Ward must be a number from 1 to 60.")

    if str(ward_id).strip() != str(ward_number):
        raise ValueError("Ward must be a whole number.")

    if not 1 <= ward_number <= 60:
        raise ValueError("Ward must be between 1 and 60.")

    # Coordinates must be supplied together.
    if (latitude is None) != (longitude is None):
        raise ValueError(
            "Provide both latitude and longitude, or neither."
        )

    if latitude is not None:
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (ValueError, TypeError, OverflowError):
            raise ValueError("Coordinates must be valid numbers.")

        if not (
            math.isfinite(latitude)
            and math.isfinite(longitude)
            and -90 <= latitude <= 90
            and -180 <= longitude <= 180
        ):
            raise ValueError("Coordinates are outside valid ranges.")


    # Validate references to saved complaint photos.
    if photo_path is not None:
        if not isinstance(photo_path, str):
            raise ValueError("Invalid photo path.")

        from modules.photo_service import UPLOAD_DIR

        photo_file = (PROJECT_ROOT / photo_path).resolve()
        upload_folder = UPLOAD_DIR.resolve()

        if photo_file.parent != upload_folder:
            raise ValueError("Photo must be in the complaint uploads folder.")

        if photo_file.suffix.lower() not in (".jpg", ".png", ".webp"):
            raise ValueError("Unsupported photo format.")

        if not photo_file.is_file():
            raise ValueError("Uploaded photo was not found.")

        # Store paths consistently using forward slashes.
        photo_path = photo_file.relative_to(PROJECT_ROOT).as_posix()


    with get_connection() as connection:
        cursor = connection.execute(
            """
                INSERT INTO civic_reports (
        title, category, description,
        ward_id, locality, location_details,
        latitude, longitude, photo_path,
        resident_id
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title.strip(),
                category,
                description.strip(),
                ward_number,
                locality.strip(),
                location_details.strip(),
                latitude,
                longitude,
                photo_path,
                resident_id,
            ),
        )

        report_id = cursor.lastrowid

        connection.execute(
            """
            INSERT INTO report_status_history (
                report_id, old_status, new_status, admin_note
            )
            VALUES (?, ?, ?, ?)
            """,
            (report_id, None, "Submitted", None),
        )

    return report_id


def get_reports(category=None, ward_id=None, status=None):
    """Retrieve civic reports with optional filters."""

    query = """
        SELECT
            report_id,
            title,
            category,
            description,
            ward_id,
            locality,
            location_details,
            latitude,
            longitude,
            photo_path,
            status,
            created_at,
            updated_at
        FROM civic_reports
        WHERE 1 = 1
    """

    parameters = []

    if category:
        if category not in REPORT_CATEGORIES:
            raise ValueError("Invalid category.")
        query += " AND category = ?"
        parameters.append(category)

    if ward_id is not None:
        if isinstance(ward_id, bool):
            raise ValueError("Invalid ward number.")
        try:
            ward_number = int(ward_id)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("Invalid ward number.")

        if not 1 <= ward_number <= 60:
            raise ValueError("Ward must be between 1 and 60.")

        query += " AND ward_id = ?"
        parameters.append(ward_number)

    if status:
        allowed_statuses = (
            "Submitted",
            "Under Review",
            "In Progress",
            "Resolved",
            "Rejected / Invalid",
        )
        if status not in allowed_statuses:
            raise ValueError("Invalid report status.")
        query += " AND status = ?"
        parameters.append(status)

    query += " ORDER BY created_at DESC, report_id DESC"

    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()

    return [dict(row) for row in rows]


def get_report_by_id(report_id):
    """Retrieve one civic report using its unique ID."""

    if isinstance(report_id, bool):
        raise ValueError("Invalid report ID.")

    try:
        report_number = int(report_id)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("Report ID must be a number.")

    if report_number <= 0:
        raise ValueError("Report ID must be positive.")

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                report_id,
                title,
                category,
                description,
                ward_id,
                locality,
                location_details,
                latitude,
                longitude,
                photo_path,
                status,
                created_at,
                updated_at
            FROM civic_reports
            WHERE report_id = ?
            """,
            (report_number,)
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def update_report_status(report_id, new_status, admin_note=None):
    """Update a civic report status and save its history."""

    allowed_statuses = (
        "Submitted",
        "Under Review",
        "In Progress",
        "Resolved",
        "Rejected / Invalid",
    )

    if new_status not in allowed_statuses:
        raise ValueError("Invalid report status.")

    if new_status == "Submitted":
        raise ValueError(
            "Submitted is an initial status and cannot be assigned again."
        )


    if isinstance(report_id, bool):
        raise ValueError("Invalid report ID.")

    try:
        report_number = int(report_id)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("Report ID must be a number.")

    if report_number <= 0:
        raise ValueError("Report ID must be positive.")

    if admin_note is not None and not isinstance(admin_note, str):
        raise ValueError("Administrative note must be text.")

    note = admin_note.strip() if admin_note else None

    if new_status == "Rejected / Invalid" and not note:
        raise ValueError("A reason is required when rejecting a report.")

    with get_connection() as connection:
        # Prevent competing status updates during this transaction.
        connection.execute("BEGIN IMMEDIATE")

        report = connection.execute(
            "SELECT status FROM civic_reports WHERE report_id = ?",
            (report_number,)
        ).fetchone()

        if report is None:
            raise ValueError("Report not found.")

        old_status = report["status"]

        if old_status == new_status:
            raise ValueError("Report already has this status.")

        # Update the current status.
        connection.execute(
            """
            UPDATE civic_reports
            SET status = ?,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE report_id = ?
            """,
            (new_status, report_number)
        )

        # Record the status change.
        connection.execute(
            """
            INSERT INTO report_status_history (
                report_id,
                old_status,
                new_status,
                admin_note
            )
            VALUES (?, ?, ?, ?)
            """,
            (report_number, old_status, new_status, note)
        )

    return True



def get_report_history(report_id):
    """Return the status history of a civic report."""

    if isinstance(report_id, bool):
        raise ValueError("Invalid report ID.")

    try:
        report_number = int(report_id)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("Report ID must be a number.")

    if report_number <= 0:
        raise ValueError("Report ID must be positive.")

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                history_id,
                report_id,
                old_status,
                new_status,
                admin_note,
                changed_at
            FROM report_status_history
            WHERE report_id = ?
            ORDER BY history_id ASC
            """,
            (report_number,)
        ).fetchall()

    return [dict(row) for row in rows]



def get_report_counts(ward_id=None):
    """Return complaint counts grouped by status."""

    statuses = (
        "Submitted",
        "Under Review",
        "In Progress",
        "Resolved",
        "Rejected / Invalid",
    )

    counts = {status: 0 for status in statuses}

    query = """
        SELECT status, COUNT(*) AS total
        FROM civic_reports
    """

    parameters = []

    if ward_id is not None:
        if isinstance(ward_id, bool):
            raise ValueError("Invalid ward ID.")

        try:
            ward_number = int(ward_id)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("Ward ID must be a number.")

        if not 1 <= ward_number <= 60:
            raise ValueError("Ward ID must be between 1 and 60.")

        query += " WHERE ward_id = ?"
        parameters.append(ward_number)

    query += " GROUP BY status"

    with get_connection() as connection:
        rows = connection.execute(
            query,
            parameters
        ).fetchall()

    for row in rows:
        counts[row["status"]] = row["total"]

    counts["Total"] = sum(counts.values())

    return counts
