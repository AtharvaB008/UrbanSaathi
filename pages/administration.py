
import hmac
import streamlit as st

st.set_page_config(
    page_title="Administration | UrbanSaathi",
    page_icon="🏛️",
    layout="wide",
)
from modules.ui_theme import apply_global_styles

apply_global_styles()

# --------------------------------------------------
# ADMIN AUTHENTICATION
# --------------------------------------------------

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False


def check_admin_credentials(username, password):
    """Check the submitted credentials against Streamlit secrets."""
    try:
        admin_config = st.secrets["admin"]
        correct_username = admin_config["username"]
        correct_password = admin_config["password"]
    except (KeyError, FileNotFoundError):
        st.error(
            "Admin credentials are not configured. "
            "Please check .streamlit/secrets.toml."
        )
        return False

    return (
        hmac.compare_digest(username, str(correct_username))
        and hmac.compare_digest(password, str(correct_password))
    )


# Show the login screen until an official is authenticated.
if not st.session_state.admin_authenticated:
    st.title("🔐 Administration Login")
    st.write(
        "Authorized municipal officials only. "
        "Please sign in to access the administration portal."
    )

    with st.form("admin_login_form"):
        username = st.text_input("Official username")
        password = st.text_input("Password", type="password")

        submitted = st.form_submit_button(
            "Sign In",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if check_admin_credentials(username, password):
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Incorrect username or password.")

    st.divider()
    st.caption("UrbanSaathi · Authorized access only")

    # Stop here so the dashboard is not displayed before login.
    st.stop()


# --------------------------------------------------
# AUTHENTICATED ADMIN DASHBOARD
# --------------------------------------------------

header_col, logout_col = st.columns([5, 1])

with header_col:
    st.title("🏛️ Administration Portal")
    st.write(
        "Urban planning, civic reports and ward-level investment diagnostics."
    )

with logout_col:
    st.write("")
    if st.button("Log out", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.rerun()

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
