
import streamlit as st
import streamlit.components.v1 as components

from modules.resident_map import create_resident_map

st.set_page_config(
    page_title="Population Density | UrbanSaathi",
    page_icon="U",
    layout="wide",
    initial_sidebar_state="collapsed",
)
from modules.ui_theme import apply_global_styles

apply_global_styles()

st.title("Population Density Map")

st.caption(
    "Explore population patterns across Mangaluru's wards. "
    "Raster units and reference year still require verification."
)

if st.button("← Back to Resident Portal"):
    st.switch_page("pages/resident.py")

try:
    population_map = create_resident_map()

    components.html(
        population_map.get_root().render(),
        height=680,
        scrolling=False,
    )

except Exception as error:
    st.error("The population map could not be loaded.")
    st.exception(error)
