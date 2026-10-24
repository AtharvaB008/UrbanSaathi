
import streamlit as st
import streamlit.components.v1 as components

from modules.resident_map import create_resident_map
from modules.facilities_map import create_facilities_map


st.set_page_config(
    page_title="City Maps | UrbanSaathi",
    page_icon="🗺️",
    layout="wide",
)

st.title("🗺️ City Maps")
st.caption(
    "Explore population patterns and mapped public facilities "
    "across Mangaluru's wards."
)

if st.button("← Back to Administration Portal"):
    st.switch_page("pages/administration.py")

st.divider()

# --------------------------------------------------
# Population Density Map
# --------------------------------------------------
st.header("1. Population Density")
st.write(
    "Explore the existing population raster across ward boundaries. "
    "Its units and reference year still require verification."
)

try:
    with st.spinner("Loading population density map..."):
        population_map = create_resident_map()

    components.html(
        population_map.get_root().render(),
        height=680,
        scrolling=False,
    )

except Exception as error:
    st.error("The population density map could not be loaded.")
    st.exception(error)

st.divider()

# --------------------------------------------------
# Facility Distribution Map
# --------------------------------------------------
st.header("2. Facility Distribution")
st.write(
    "Explore mapped healthcare, education, parks and public "
    "transport facilities. Use the map controls to toggle layers."
)

refresh_facilities = st.button(
    "Refresh facility data",
    key="refresh_admin_facilities",
)

try:
    with st.spinner("Loading facility distribution map..."):
        facility_map, counts = create_facilities_map(
            refresh=refresh_facilities
        )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Healthcare",
        counts.get("Healthcare", 0),
    )
    col2.metric(
        "Education",
        counts.get("Education", 0),
    )
    col3.metric(
        "Parks",
        counts.get("Parks", 0),
    )
    col4.metric(
        "Bus Stops & Stations",
        counts.get("Bus Stops & Stations", 0),
    )

    components.html(
        facility_map.get_root().render(),
        height=650,
        scrolling=True,
    )

except Exception as error:
    st.error("The facility distribution map could not be loaded.")
    st.exception(error)

st.caption("UrbanSaathi · Mangaluru, Karnataka · Administration Portal")
