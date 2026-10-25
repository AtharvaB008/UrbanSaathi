
import html
import json
import os
from pathlib import Path

import folium
import geopandas as gpd
import requests
from dotenv import load_dotenv
from folium.plugins import MarkerCluster
from shapely.geometry import Point

from modules.data_loader import load_wards

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = PROJECT_ROOT / "data" / "mangaluru_facilities_cache.json"

OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
CITY_CENTER = [12.9141, 74.8560]

CATEGORIES = {
    "Healthcare": {
        "color": "red",
        "amenities": {"hospital", "clinic", "doctors", "pharmacy"},
    },
    "Education": {
        "color": "blue",
        "amenities": {"school", "college", "university"},
    },
    "Parks": {
        "color": "green",
        "amenities": set(),
    },
    "Bus Stops & Stations": {
        "color": "purple",
        "amenities": {"bus_station"},
    },
}


def fetch_facilities(refresh=False):
    """Load cached OpenStreetMap data or fetch it from Overpass."""
    if CACHE_FILE.exists() and not refresh:
        try:
            with CACHE_FILE.open("r", encoding="utf-8") as file:
                cached = json.load(file)
            if cached.get("elements") is not None:
                return cached["elements"]
        except (OSError, json.JSONDecodeError):
            pass

    wards = load_wards()
    west, south, east, north = wards.total_bounds

    query = f"""
    [out:json][timeout:60];
    (
      nwr["amenity"~"^(hospital|clinic|doctors|pharmacy|school|college|university|bus_station)$"]({south},{west},{north},{east});
      nwr["leisure"="park"]({south},{west},{north},{east});
      nwr["highway"="bus_stop"]({south},{west},{north},{east});
    );
    out center tags;
    """

    response = requests.post(
        OVERPASS_URL,
        data={"data": query},
        headers={"User-Agent": "UrbanSaathi/1.0 (local prototype)"},
        timeout=90,
    )
    response.raise_for_status()
    elements = response.json().get("elements", [])

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = CACHE_FILE.with_suffix(".tmp")
    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump({"elements": elements}, file)
    temporary_file.replace(CACHE_FILE)

    return elements


def classify_facility(tags):
    amenity = tags.get("amenity", "")
    leisure = tags.get("leisure", "")
    highway = tags.get("highway", "")

    if amenity in CATEGORIES["Healthcare"]["amenities"]:
        return "Healthcare"
    if amenity in CATEGORIES["Education"]["amenities"]:
        return "Education"
    if leisure == "park":
        return "Parks"
    if amenity == "bus_station" or highway == "bus_stop":
        return "Bus Stops & Stations"

    return None


def create_facilities_map(refresh=False):
    """Create an interactive facilities map within Mangaluru's wards."""
    wards = load_wards()
    elements = fetch_facilities(refresh=refresh)

    carto_key = os.getenv("CARTO_API_KEY")
    if not carto_key:
        raise ValueError("CARTO_API_KEY is missing from your local .env file.")

    city_map = folium.Map(
        location=CITY_CENTER,
        zoom_start=12,
        tiles=None,
        control_scale=True,
    )

    folium.TileLayer(
        tiles=(
            "https://basemaps.cartocdn.com/rastertiles/voyager/"
            f"{{z}}/{{x}}/{{y}}.png?key={carto_key}"
        ),
        attr="© OpenStreetMap contributors © CARTO",
        name="CARTO Voyager",
        overlay=False,
        control=True,
    ).add_to(city_map)

    ward_union = wards.geometry.union_all()
    ward_layer = folium.FeatureGroup(
        name="Mangaluru Ward Boundaries",
        show=True,
    )

    folium.GeoJson(
        wards,
        name="Ward boundaries",
        style_function=lambda feature: {
            "color": "#263238",
            "weight": 1.3,
            "fillColor": "#80CBC4",
            "fillOpacity": 0.08,
        },
        highlight_function=lambda feature: {
            "weight": 3,
            "color": "#FF9800",
            "fillOpacity": 0.2,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["KGISWardNo"],
            aliases=["Ward number:"],
            sticky=True,
        ),
    ).add_to(ward_layer)
    ward_layer.add_to(city_map)

    layers = {}
    counts = {name: 0 for name in CATEGORIES}

    for category, settings in CATEGORIES.items():
        layer = folium.FeatureGroup(name=category, show=True)
        cluster = MarkerCluster()
        cluster.add_to(layer)
        layer.add_to(city_map)
        layers[category] = cluster

    seen = set()

    for item in elements:
        item_id = (item.get("type"), item.get("id"))
        if item_id in seen:
            continue
        seen.add(item_id)

        tags = item.get("tags", {})
        category = classify_facility(tags)
        if category is None:
            continue

        if "lat" in item and "lon" in item:
            lat, lon = item["lat"], item["lon"]
        elif "center" in item:
            lat = item["center"]["lat"]
            lon = item["center"]["lon"]
        else:
            continue

        if not ward_union.covers(Point(lon, lat)):
            continue

        name = tags.get("name", "Unnamed facility")
        facility_type = (
            tags.get("amenity")
            or tags.get("leisure")
            or tags.get("highway")
            or "Unknown"
        )

        popup_html = (
            f"<b>{html.escape(name)}</b><br>"
            f"<b>Category:</b> {html.escape(category)}<br>"
            f"<b>Type:</b> {html.escape(facility_type)}"
        )

        folium.Marker(
            location=[lat, lon],
            tooltip=name,
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(
                color=CATEGORIES[category]["color"],
                icon="info-sign",
            ),
        ).add_to(layers[category])

        counts[category] += 1

    folium.LayerControl(collapsed=False).add_to(city_map)
    city_map.fit_bounds(wards.total_bounds[[1, 0, 3, 2]].reshape(2, 2).tolist())

    return city_map, counts
