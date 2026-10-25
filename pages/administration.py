
import streamlit as st

st.set_page_config(
    page_title="Administration | UrbanSaathi",
    page_icon="🏛️",
    layout="wide",
)

if st.button("← Back to Home"):
    st.switch_page("app.py")

st.title("🏛️ Administration Portal")
st.write(
    "Urban planning, civic reports and ward-level investment diagnostics."
)

st.divider()

st.subheader("City Planning Tools")


map_col, diagnostics_col, compression_col = st.columns(3, gap="large")

with map_col:
    st.markdown("### 🗺️ City Map")
    st.write(
        "Explore Mangaluru wards and inspect mapped public facilities."
    )
    if st.button("Open City Map", use_container_width=True):
        st.switch_page("pages/admin_map.py")

with diagnostics_col:
    st.markdown("### 📊 Ward Diagnostics")
    st.write(
        "Compare healthcare, education, parks and bus-stop counts "
        "across wards."
    )
    if st.button("Open Ward Diagnostics", use_container_width=True):
        st.switch_page("pages/diagnostics.py")


with compression_col:
    st.markdown("### 📈 Ward Comparison")
    st.write(
        "Compare ward-level facility counts and overall priority scores "
        "using interactive charts."
    )
    if st.button("Open Ward Comparison", use_container_width=True):
        st.switch_page("pages/ward_comparison.py")



st.divider()

st.subheader("Data status")

st.info(
    "Facility counts are based on mapped records within ward boundaries. "
    "Population-based investment scores are not enabled because the "
    "population raster's source, units and reference year still need "
    "verification."
)

st.caption("UrbanSaathi · Mangaluru, Karnataka · Hackathon Prototype")
