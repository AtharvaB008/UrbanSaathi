
import streamlit as st
import pandas as pd

from shapely.geometry import Point
from modules.data_loader import load_wards
from modules.facilities_map import fetch_facilities, classify_facility

st.set_page_config(
    page_title="Find Your Ideal Ward | UrbanSaathi",
    page_icon="🏡",
    layout="wide",
)
from modules.ui_theme import apply_global_styles

apply_global_styles()

st.title("✨ Find Your Ideal Ward")
st.write(
    "Choose what matters most to you. We'll compare available "
    "facilities across wards and recommend the strongest matches."
)

st.caption("Set a priority to 0 if it does not matter to you.")

st.subheader("1. Your priorities")

healthcare = st.slider("Healthcare access", 0, 5, 5)
education = st.slider("Schools and education", 0, 5, 4)
parks = st.slider("Parks and green spaces", 0, 5, 3)
transport = st.slider("Public transport", 0, 5, 4)

if st.button("Find My Best-Matched Wards", type="primary"):
    try:
        wards = load_wards()
        facilities = fetch_facilities()

        if wards is None or wards.empty:
            st.error("Ward boundary data is unavailable.")
            st.stop()

        if facilities is None or len(facilities) == 0:
            st.error("Facility data is unavailable. Please try again later.")
            st.stop()

        # Normalize facility records to a DataFrame.
        if isinstance(facilities, dict):
            facility_records = facilities.get("elements", [])
            facilities_df = pd.DataFrame(facility_records)
        elif isinstance(facilities, pd.DataFrame):
            facilities_df = facilities.copy()
        else:
            facilities_df = pd.DataFrame(facilities)

        if facilities_df.empty:
            st.error("No facility records were returned.")
            st.stop()

        # Detect common latitude/longitude formats.
        lat_col = next(
            (c for c in ["lat", "latitude"] if c in facilities_df.columns),
            None,
        )
        lon_col = next(
            (c for c in ["lon", "lng", "longitude"] if c in facilities_df.columns),
            None,
        )

        # Overpass-style records may store coordinates in "center"
        # or a nested geometry; those need separate handling.
        if not lat_col or not lon_col:
            st.error(
                "Facility records do not expose latitude and longitude "
                "in the expected format. We need to adapt this page to "
                "the format returned by fetch_facilities()."
            )
            st.stop()

        # Classify facilities using the project's existing classifier.
        facilities_df["_category"] = facilities_df.apply(
            lambda row: classify_facility(
                row.get("tags", {})
                if isinstance(row.get("tags", {}), dict)
                else {}
            ),
            axis=1,
        )

        # Build ward-by-ward counts using actual ward geometries.
        results = []

        category_preferences = {
            "Healthcare": healthcare,
            "Education": education,
            "Parks": parks,
            "Bus Stops & Stations": transport,
        }

        for _, ward in wards.iterrows():
            geometry = ward.get("geometry")

            if geometry is None or geometry.is_empty:
                continue

            counts = {category: 0 for category in category_preferences}

            for _, facility in facilities_df.iterrows():
                try:
                    lat = float(facility[lat_col])
                    lon = float(facility[lon_col])
                    point = Point(lon, lat)

                    if geometry.covers(point):
                        category = facility["_category"]
                        if category in counts:
                            counts[category] += 1
                except (TypeError, ValueError):
                    continue

            results.append({
                "Ward": (
    str(ward["KGISWardNa"]).strip()
    if pd.notna(ward.get("KGISWardNa"))
    and str(ward["KGISWardNa"]).strip()
    else f"Ward {ward.get('KGISWardNo', ward.get('KGISWardID', 'Unknown'))}"
),
                "Ward number": ward.get("KGISWardNo", "Unknown"),
                **counts,
            })

        ranking = pd.DataFrame(results)

        if ranking.empty:
            st.error(
                "No wards could be matched. Check that ward geometries "
                "are available and use the same coordinate reference system."
            )
            st.stop()

        # Normalize each facility category so categories with large
        # raw counts do not automatically dominate the score.
        score = pd.Series(0.0, index=ranking.index)
        total_weight = sum(category_preferences.values())

        if total_weight == 0:
            st.warning("Choose a priority above 0 to generate recommendations.")
            st.stop()

        for category, weight in category_preferences.items():
            max_count = ranking[category].max()

            if weight > 0 and max_count > 0:
                score += (ranking[category] / max_count) * weight

        ranking["Match score"] = (score / total_weight * 100).round(1)
        ranking = ranking.sort_values(
            "Match score",
            ascending=False,
        ).reset_index(drop=True)

        st.subheader("2. Your best-matched wards")
        st.caption(
            "Rankings use relative facility counts and your selected "
            "priorities. They do not measure facility quality, capacity, "
            "travel time, or population-adjusted access."
        )

        display_columns = [
            "Ward",
            "Ward number",
            "Healthcare",
            "Education",
            "Parks",
            "Bus Stops & Stations",
            "Match score",
        ]

        st.dataframe(
            ranking[display_columns].head(5),
            use_container_width=True,
            hide_index=True,
        )

        best = ranking.iloc[0]

        st.success(
            f"Your strongest match is {best['Ward']} "
            f"with a preference match score of {best['Match score']}%."
        )

        st.subheader("Why this ward matched")
        reasons = []

        for category, weight in category_preferences.items():
            if weight > 0:
                reasons.append(
                    f"- **{category}:** {int(best[category])} mapped facilities "
                    f"(your priority: {weight}/5)"
                )

        st.markdown("\n".join(reasons))

        st.info(
            "These are preliminary recommendations based on mapped facility "
            "counts. Review the listed facilities and local conditions before "
            "making a housing or relocation decision."
        )

    except Exception as error:
        st.error(f"Could not generate ward recommendations: {error}")

if st.button("← Back to Resident Portal"):
    st.switch_page("pages/resident.py")
