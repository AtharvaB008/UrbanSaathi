
import sqlite3
from pathlib import Path

# Shared database location
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "urbansaathi.db"


def get_connection():
    """Create a connection to the shared SQLite database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_database():
    """Create the required tables if they do not already exist."""

    with get_connection() as connection:

        connection.executescript("""
            CREATE TABLE IF NOT EXISTS wards (
                ward_id INTEGER PRIMARY KEY
                    CHECK (ward_id BETWEEN 1 AND 60),
                ward_name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS facilities (
                facility_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ward_id INTEGER,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                latitude REAL NOT NULL
                    CHECK (latitude BETWEEN -90 AND 90),
                longitude REAL NOT NULL
                    CHECK (longitude BETWEEN -180 AND 180),
                source TEXT NOT NULL,
                source_date TEXT,
                FOREIGN KEY (ward_id) REFERENCES wards(ward_id)
            );

            CREATE TABLE IF NOT EXISTS indicators (
                indicator_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ward_id INTEGER NOT NULL,
                indicator_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                source TEXT NOT NULL,
                reference_date TEXT NOT NULL,
                calculation_method TEXT,
                coverage_notes TEXT,
                FOREIGN KEY (ward_id) REFERENCES wards(ward_id),
                UNIQUE (ward_id, indicator_name, reference_date, source)
            );

            CREATE TABLE IF NOT EXISTS civic_reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK (length(trim(title)) > 0),
                category TEXT NOT NULL CHECK (
                    category IN (
                        'Water',
                        'Electricity / street lighting',
                        'Roads & public property',
                        'Waste & sanitation',
                        'Drainage & waterlogging',
                        'Other civic issue'
                    )
                ),
                description TEXT NOT NULL
                    CHECK (length(trim(description)) > 0),
                ward_id INTEGER NOT NULL,
                locality TEXT NOT NULL
                    CHECK (length(trim(locality)) > 0),
                location_details TEXT NOT NULL
                    CHECK (length(trim(location_details)) > 0),
                latitude REAL CHECK (latitude BETWEEN -90 AND 90),
                longitude REAL CHECK (longitude BETWEEN -180 AND 180),
                photo_path TEXT,
                resident_id TEXT,
                status TEXT NOT NULL DEFAULT 'Submitted'
                    CHECK (
                        status IN (
                            'Submitted',
                            'Under Review',
                            'In Progress',
                            'Resolved',
                            'Rejected / Invalid'
                        )
                    ),
                created_at TEXT NOT NULL
                    DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                updated_at TEXT NOT NULL
                    DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                CHECK (
                    (latitude IS NULL AND longitude IS NULL)
                    OR
                    (latitude IS NOT NULL AND longitude IS NOT NULL)
                ),
                FOREIGN KEY (ward_id) REFERENCES wards(ward_id)
            );

            CREATE TABLE IF NOT EXISTS report_status_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                old_status TEXT,
                new_status TEXT NOT NULL CHECK (
                    new_status IN (
                        'Submitted',
                        'Under Review',
                        'In Progress',
                        'Resolved',
                        'Rejected / Invalid'
                    )
                ),
                admin_note TEXT,
                changed_at TEXT NOT NULL
                    DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                CHECK (
                    new_status != 'Rejected / Invalid'
                    OR length(trim(coalesce(admin_note, ''))) > 0
                ),
                FOREIGN KEY (report_id)
                    REFERENCES civic_reports(report_id)
                    ON DELETE CASCADE
            );
        """)
        # Add Resident ID support to existing databases.
        existing_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(civic_reports)"
            ).fetchall()
        }

        if "resident_id" not in existing_columns:
            connection.execute(
                "ALTER TABLE civic_reports ADD COLUMN resident_id TEXT"
            )

        # Insert the 60 agreed ward numbers only if missing.
        connection.executemany(
            """
            INSERT OR IGNORE INTO wards (ward_id, ward_name)
            VALUES (?, ?)
            """,
            [(i, str(i)) for i in range(1, 61)]
        )

    print("UrbanSaathi database initialized successfully!")
    print(f"Database location: {DB_PATH}")


if __name__ == "__main__":
    init_database()
