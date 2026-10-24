from modules.data_loader import load_wards
import streamlit as st

st.set_page_config(
    page_title="Resident Portal | UrbanSaathi",
    page_icon="U",
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
        padding: 2.5rem;
        border-radius: 18px;
        margin: 1rem 0 2rem;
        color: white;
    }

    .hero h1 {
        color: white;
        font-size: 2.5rem;
        margin: 0.7rem 0;
    }

    .hero p {
        color: #E0F2F1;
        font-size: 1.05rem;
        margin-bottom: 0;
        line-height: 1.7;
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
        padding: 1.3rem;
        min-height: 175px;
    }

    .feature-card h3 {
        color: #153F3B;
        font-size: 1.15rem;
    }

    .feature-card p {
        color: #60736F;
        font-size: 0.94rem;
        line-height: 1.6;
    }

    
    .section-note {
        color: #465F5A;
        font-size: 0.95rem;
    }

    /* Improve readability of headings and metric values */
    .stApp h2,
    .stApp h3 {
        color: #153F3B;
    }

    .stApp [data-testid="stMetricLabel"],
    .stApp [data-testid="stMetricValue"],
    .stApp [data-testid="stMetricDelta"] {
        color: #153F3B;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# Top navigation
nav_left, nav_right = st.columns([5, 1])

with nav_left:
    st.markdown("### UrbanSaathi | Resident Portal")

with nav_right:
    if st.button("Home", use_container_width=True):
        st.rerun()

# Welcome section
st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">YOUR CITY, YOUR COMMUNITY</div>
        <h1>Discover Mangaluru</h1>
        <p>
            Understand your neighbourhood, explore public facilities,
            compare wards and help build a better city.
            UrbanSaathi brings city information together to help residents
            make more informed decisions.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# Overview
st.subheader("Mangaluru at a glance")

st.markdown(
    """
    <p class="section-note">
        Explore population patterns, public facilities and neighbourhood
        information through the tools below. Indicators will be added
        as their data sources and coverage are verified.
    </p>
    """,
    unsafe_allow_html=True,
)

# Load the ward count from the actual dataset
try:
    wards = load_wards()
    ward_count = wards["KGISWardID"].nunique()
    ward_status = "Loaded from ward data"
except Exception as error:
    ward_count = "Unavailable"
    ward_status = "Ward data could not be loaded"
    st.warning(f"Unable to load ward information: {error}")

metric1, metric2, metric3 = st.columns(3)

with metric1:
    st.metric(
        "Ward boundaries",
        ward_count,
        help=ward_status,
    )

with metric2:
    st.metric(
        "City indicators",
        "In development",
        help="Verified population and facility indicators will appear here.",
    )

with metric3:
    st.metric(
        "Resident tools",
        "4",
        help="Population map, facilities, ward comparison and civic issues.",
    )

st.caption(
    "Data note: ward boundaries are loaded from the current project dataset. "
    "Population units, reference year and facility coverage still require verification."
)

# Main features
st.subheader("Explore UrbanSaathi")
st.write(
    "Choose a tool to explore Mangaluru or share information about "
    "a civic issue."
)

row1_col1, row1_col2 = st.columns(2, gap="large")

with row1_col1:
    st.markdown(
        """
        <div class="feature-card">
            <h3>1. Population Density Map</h3>
            <p>
                Explore population distribution across Mangaluru's wards
                using an interactive map.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(
        "Open Population Map",
        key="population_map",
        use_container_width=True,
    ):
        st.switch_page("pages/population_map.py")
        
with row1_col2:
    st.markdown(
        """
        <div class="feature-card">
            <h3>2. Facilities Explorer</h3>
            <p>
                Explore healthcare, education, parks and public transport
                facilities across the city.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Explore Facilities", key="facilities", use_container_width=True):
        st.info("The facilities explorer will be connected in a later step.")

row2_col1, row2_col2 = st.columns(2, gap="large")

with row2_col1:
    st.markdown(
        """
        <div class="feature-card">
            <h3>3. Compare Neighbourhoods</h3>
            <p>
                Compare wards using population patterns, facility access
                and other verified neighbourhood indicators.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Compare Wards", key="compare_wards", use_container_width=True):
        st.info("Ward comparisons and neighbourhood insights are planned next.")

with row2_col2:
    st.markdown(
        """
        <div class="feature-card">
            <h3>4. Civic Issues Register</h3>
            <p>
                Report local civic issues and, when the reporting system
                is connected, track their status.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open Civic Issues", key="civic_issues", use_container_width=True):
        st.info("Civic issue reporting will be connected to the shared backend.")

st.divider()


st.divider()
st.subheader("Explore UrbanSaathi")

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### Population Density Map")
    st.write(
        "Explore population distribution across Mangaluru's wards."
    )
    if st.button(
        "Open Population Map",
        key="population_map",
        use_container_width=True,
    ):
        st.switch_page("pages/population_map.py")

with col2:
    st.markdown("### Facilities Distribution Map")
    st.write(
        "Explore healthcare, education, parks and public transport."
    )
    if st.button(
        "Open Facilities Map",
        key="facilities_map",
        use_container_width=True,
    ):
        st.switch_page("pages/facilities.py")

st.caption(
    "UrbanSaathi | Mangaluru, Karnataka | Hackathon prototype"
)
