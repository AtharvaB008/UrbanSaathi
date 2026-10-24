
import streamlit as st

st.set_page_config(
    page_title="Administration | UrbanSaathi",
    page_icon="🏛️",
    layout="wide",
)

st.title("🏛️ Administration Portal")
st.write(
    "Urban planning, civic reports and ward-level investment diagnostics."
)

st.divider()
st.subheader("City Planning Tools")

map_col, diagnostics_col, comparison_col = st.columns(3, gap="large")

with map_col:
    st.markdown("### 🗺️ City Map")
    st.write("Explore Mangaluru wards and mapped public facilities.")
    if st.button("Open City Map", use_container_width=True):
        st.switch_page("pages/city_maps.py")

with diagnostics_col:
    st.markdown("### 📊 Ward Diagnostics")
    st.write(
        "Investigate the distribution of healthcare, education, "
        "parks and bus stops across wards."
    )
    if st.button("Open Ward Diagnostics", use_container_width=True):
        st.switch_page("pages/diagnostics.py")

with comparison_col:
    st.markdown("### 📈 Ward Comparison")
    st.write(
        "Compare facility counts and investigate possible "
        "service gaps between wards."
    )
    if st.button("Open Ward Comparison", use_container_width=True):
        st.switch_page("pages/ward_comparison.py")

st.divider()
st.subheader("Civic Complaint Management")
st.write(
    "View resident complaints, update their statuses, "
    "and review complaint statistics."
)

if st.button("Manage Civic Reports", use_container_width=True):
    st.switch_page("pages/manage_reports.py")

st.divider()
st.subheader("Data Status")
st.info(
    "Facility counts are based on mapped records within ward boundaries. "
    "Population-based investment scores are not enabled because the "
    "population raster's source, units and reference year still need "
    "verification."
)

st.caption("UrbanSaathi · Mangaluru, Karnataka · Hackathon Prototype")
