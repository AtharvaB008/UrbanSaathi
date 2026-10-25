
import streamlit as st
import streamlit.components.v1 as components

from modules.facilities_map import create_facilities_map

st.set_page_config(
    page_title="UrbanSaathi | Facilities",
    page_icon="🏙️",
    layout="wide",
)

st.title("Facilities Distribution")
st.caption(
    "Explore healthcare, education, parks, and public transport "
    "facilities across Mangaluru."
)

if st.button("← Back to Resident Portal"):
    st.switch_page("pages/resident.py")

refresh = st.button("Refresh facility data")

try:
    city_map, counts = create_facilities_map(refresh=refresh)

    st.subheader("Facility Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Healthcare", counts.get("Healthcare", 0))
    col2.metric("Education", counts.get("Education", 0))
    col3.metric("Parks", counts.get("Parks", 0))
    col4.metric(
        "Bus Stops & Stations",
        counts.get("Bus Stops & Stations", 0),
    )

    components.html(
        city_map.get_root().render(),
        height=650,
        scrolling=True,
    )

except Exception as error:
    st.error("Could not load the facilities map.")
    st.caption(f"Details: {error}")