
import streamlit as st

st.set_page_config(
    page_title="UrbanSaathi | Mangaluru",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        /* Hide the dark left sidebar and its navigation */
        [data-testid="stSidebar"] {
            display: none !important;
        }

        /* Remove the black top header bar */
        [data-testid="stHeader"] {
            display: none !important;
        }

        /* Hide the top toolbar */
        [data-testid="stToolbar"] {
            display: none !important;
        }

        /* Remove the decorative top strip */
        [data-testid="stDecoration"] {
            display: none !important;
        }

        /* Let the homepage use the full available width */
        [data-testid="stAppViewContainer"] > .main {
            margin-left: 0 !important;
        }

        .block-container {
            max-width: 100% !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <style>
    .stApp {
        background-color: #F6F9F8;
    }

    .block-container {
        max-width: 1100px;
        padding-top: 3rem;
        padding-bottom: 3rem;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    .hero {
        text-align: center;
        padding: 2.5rem 1rem 2rem;
    }

    .hero .eyebrow {
        color: #137C72;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 3px;
        text-transform: uppercase;
    }

    .hero h1 {
        color: #153F3B;
        font-size: 3.5rem;
        margin: 0.7rem 0;
    }

    .hero p {
        color: #5A706D;
        font-size: 1.15rem;
    }

    .portal-card {
        background: white;
        border: 1px solid #DDE9E6;
        border-radius: 18px;
        padding: 1.5rem;
        min-height: 230px;
    }

    .portal-icon {
        font-size: 2.4rem;
        margin-bottom: 0.5rem;
    }

    .portal-card h3 {
        color: #153F3B;
    }

    .portal-card p {
        color: #60736F;
        min-height: 70px;
    }

    div.stButton > button {
        width: 100%;
        min-height: 3rem;
        border-radius: 10px;
        border: 1px solid #167D75;
        font-weight: 600;
    }

    .footer-note {
        text-align: center;
        color: #7A8C88;
        font-size: 0.85rem;
        margin-top: 3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Urban Intelligence Platform</div>
        <h1>UrbanSaathi</h1>
        <p>
            Understand your city. Discover your neighbourhood.
            <br>
            Building a better Mangaluru, together.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Choose your portal")
st.write("Select the experience that matches your role.")

st.write("")

resident_col, admin_col = st.columns(2, gap="large")

with resident_col:
    st.markdown(
        """
        <div class="portal-card">
            <div class="portal-icon">🏘️</div>
            <h3>Resident Portal</h3>
            <p>
                Explore population patterns, discover nearby
                facilities, compare wards and raise civic issues.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(
        "Enter Resident Portal →",
        key="resident_portal",
        type="primary",
    ):
        st.switch_page("pages/resident.py")

with admin_col:
    st.markdown(
        """
        <div class="portal-card">
            <div class="portal-icon">🏛️</div>
            <h3>Administration Portal</h3>
            <p>
                Review civic reports, identify underserved wards,
                examine priority scores and support urban planning.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(
        "Enter Administration Portal →",
        key="admin_portal",
    ):
        st.switch_page("pages/administration.py")

st.markdown(
    """
    <div class="footer-note">
        UrbanSaathi · Mangaluru, Karnataka · Hackathon Prototype
    </div>
    """,
    unsafe_allow_html=True,
)
