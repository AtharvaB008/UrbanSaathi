
import streamlit as st
import streamlit.components.v1 as components

from modules.resident_map import create_resident_map

st.set_page_config(
    page_title="Resident Portal | UrbanSaathi",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp {
        background: #F6F9F8;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    .hero {
        background: linear-gradient(120deg, #123B3A, #167D75);
        padding: 2rem 2.2rem;
        border-radius: 18px;
        margin: 1rem 0 1.5rem;
        color: white;
    }

    .hero h1 {
        color: white;
        font-size: 2.4rem;
        margin: 0.5rem 0;
    }

    .hero p {
        color: #E0F2F1;
        font-size: 1.05rem;
        margin-bottom: 0;
    }

    .eyebrow {
        color: #A7F3D0;
        letter-spacing: 2px;
        font-size: 0.8rem;
        font-weight: 700;
    }

    .feature-card {
        background: white;
        border: 1px solid #DCE9E6;
        border-radius: 14px;
        padding: 1.1rem;
        min-height: 145px;
    }

    .feature-card h3 {
        color: #153F3B;
        font-size: 1.1rem;
    }

    .feature-card p {
        color: #60736F;
        font-size: 0.92rem;
    }

    .section-note {
        color: #60736F;
        font-size: 0.92rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Top navigation
nav_left, nav_right = st.columns([5, 1])

with nav_left:
    st.markdown("### 🏙️ UrbanSaathi")

with nav_right:
    if st.button("← Home", use_container_width=True):
        st.switch_page("app.py")

# Welcome banner
st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">RESIDENT PORTAL · MANGALURU</div>
        <h1>Your neighbourhood, at a glance.</h1>
        <p>
            Explore your city, discover local facilities,
            and make informed neighbourhood decisions.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Summary cards
st.subheader("Your city overview")

metric1, metric2, metric3 = st.columns(3)

with metric1:
    st.metric("Ward boundaries", "60")
    st.caption("Ward geometries available in the prototype")

with metric2:
    st.metric("Population explorer", "Ready")
    st.caption("Interactive population raster")

with metric3:
    st.metric("Facilities explorer", "Coming next")
    st.caption("A separate map experience")

st.divider()

# Main population map
st.subheader("🗺️ Population Density Explorer")

st.markdown(
    '<p class="section-note">'
    'Explore the population raster and Mangaluru ward boundaries. '
    'The raster units and reference year remain provisional.'
    '</p>',
    unsafe_allow_html=True,
)

try:
    population_map = create_resident_map()

    components.html(
        population_map.get_root().render(),
        height=650,
        scrolling=False,
    )

except Exception:
    st.error("The population map could not be loaded.")
    st.exception(Exception("Check the terminal for the underlying error."))

st.divider()

# Other resident features
st.subheader("Explore more")

st.write(
    "Continue exploring Mangaluru through these separate resident tools."
)

feature1, feature2 = st.columns(2, gap="large")

with feature1:
    st.markdown(
        """
        <div class="feature-card">
            <h3>📍 Facilities Explorer</h3>
            <p>
                Explore healthcare, education, parks and
                public transport on a dedicated facilities map.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Open Facilities Explorer", use_container_width=True):
        st.info("The separate facilities map is the next integration task.")

with feature2:
    st.markdown(
        """
        <div class="feature-card">
            <h3>⚖️ Compare Neighbourhoods</h3>
            <p>
                Compare wards and understand differences in
                population patterns and facility access.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Compare Wards", use_container_width=True):
        st.info("Ward comparison will be connected after the map details.")

feature3, feature4 = st.columns(2, gap="large")

with feature3:
    st.markdown(
        """
        <div class="feature-card">
            <h3>📝 Civic Reports</h3>
            <p>
                Report local issues and help bring neighbourhood
                concerns to the attention of city administrators.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Explore Civic Reports", use_container_width=True):
        st.info("Civic report submission will connect to the shared report service.")

with feature4:
    st.markdown(
        """
        <div class="feature-card">
            <h3>🏡 Neighbourhood Insights</h3>
            <p>
                Discover useful information about wards,
                local facilities and urban conditions.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Explore Insights", use_container_width=True):
        st.info("Neighbourhood insights will be built on verified data.")

st.divider()

st.caption(
    "UrbanSaathi · Mangaluru, Karnataka · Hackathon prototype"
)
