"""
UrbanSaathi — Facilities Database Synchronization

Assigns OpenStreetMap facilities to Mangaluru wards
before storing them in SQLite.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from modules.data_loader import load_wards
from modules.facilities_map import fetch_facilities, classify_facility
from shapely.geometry import Point


def get_facility_coordinates(facility):
    """Extract coordinates from an OSM node, way, or relation."""

    latitude = facility.get("lat")
    longitude = facility.get("lon")

    if latitude is None or longitude is None:
        center = facility.get("center") or {}
        latitude = center.get("lat")
        longitude = center.get("lon")

    if latitude is None or longitude is None:
        return None

    return float(latitude), float(longitude)


def find_facility_ward(latitude, longitude, wards):
    """Return the ward number containing a facility."""

    point = Point(longitude, latitude)

    for _, ward in wards.iterrows():
        if ward.geometry.covers(point):
            return int(ward["KGISWardNo"])

    return None

def sync_facilities_to_database():
    """
    Synchronize ward-matched OSM facilities with SQLite.

    Replaces the previously imported facility snapshot
    in a single transaction.

    Does not modify wards, indicators, or civic reports.
    """

    project_root = Path(__file__).resolve().parent.parent
    database_path = project_root / "database" / "urbansaathi.db"

    if not database_path.is_file():
        raise FileNotFoundError(
            "UrbanSaathi database not found. "
            "Initialize the database before synchronizing."
        )

    wards = load_wards()
    facilities = fetch_facilities()

    source_date = datetime.now(timezone.utc).date().isoformat()

    records = []
    seen_osm_ids = set()
    excluded = 0

    for facility in facilities:
        osm_id = (facility.get("type"), facility.get("id"))

        if osm_id in seen_osm_ids:
            continue

        seen_osm_ids.add(osm_id)

        category = classify_facility(
            facility.get("tags", {})
        )

        coordinates = get_facility_coordinates(facility)

        if category is None or coordinates is None:
            excluded += 1
            continue

        latitude, longitude = coordinates

        ward_id = find_facility_ward(
            latitude,
            longitude,
            wards,
        )

        if ward_id is None:
            excluded += 1
            continue

        tags = facility.get("tags") or {}

        name = tags.get("name") or (
            f"Unnamed {category} facility"
        )

        records.append((
            ward_id,
            name,
            category,
            latitude,
            longitude,
            "OpenStreetMap",
            source_date,
        ))

    connection = sqlite3.connect(database_path)

    try:
        with connection:
            # Replace only the OSM snapshot managed here.
            connection.execute(
                "DELETE FROM facilities WHERE source = ?",
                ("OpenStreetMap",),
            )

            connection.executemany(
                """
                INSERT INTO facilities (
                    ward_id,
                    name,
                    category,
                    latitude,
                    longitude,
                    source,
                    source_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )

    finally:
        connection.close()

    return {
        "imported": len(records),
        "excluded": excluded,
        "source_date": source_date,
    }