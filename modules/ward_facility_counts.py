
"""Count mapped facilities inside each Mangaluru ward."""

from collections import Counter

import geopandas as gpd
from shapely.geometry import Point

from modules.data_loader import load_wards
from modules.facilities_map import fetch_facilities, classify_facility


CATEGORY_COLUMNS = {
    "Healthcare": "healthcare_count",
    "Education": "education_count",
    "Parks": "parks_count",
    "Bus Stops & Stations": "transport_count",
}


def build_ward_facility_counts(refresh=False):
    """Return wards with facility counts assigned by geographic location.

    Counts are based on facilities returned by the existing map data source.
    They are mapped counts, not a guarantee of complete real-world coverage.
    """
    wards = load_wards().copy()
    elements = fetch_facilities(refresh=refresh)

    # Use a projected CRS for robust geographic operations where possible.
    wards = wards.to_crs("EPSG:4326")

    counts_by_ward = {
        ward_id: Counter()
        for ward_id in wards["KGISWardID"]
    }

    # Ensure point-in-polygon matching uses the same geographic CRS.
    for item in elements:
        tags = item.get("tags", {})
        category = classify_facility(tags)

        if category not in CATEGORY_COLUMNS:
            continue

        # Only count bus stops here; don't count railway/metro features.
        if category == "Bus Stops & Stations":
            if tags.get("highway") != "bus_stop":
                continue

        if "lat" in item and "lon" in item:
            lat, lon = item["lat"], item["lon"]
        elif "center" in item:
            lat = item["center"]["lat"]
            lon = item["center"]["lon"]
        else:
            continue

        point = Point(float(lon), float(lat))

        matching = wards[wards.geometry.covers(point)]

        if matching.empty:
            continue

        # A point on a shared ward boundary may match more than one ward.
        # Avoid arbitrary double-counting in that case.
        if len(matching) != 1:
            continue

        ward_id = matching.iloc[0]["KGISWardID"]
        counts_by_ward[ward_id][category] += 1

    for category, column in CATEGORY_COLUMNS.items():
        wards[column] = [
            counts_by_ward[ward_id].get(category, 0)
            for ward_id in wards["KGISWardID"]
        ]

    return wards
