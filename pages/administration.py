
import streamlit as st

st.set_page_config(
    page_title="Administration | UrbanSaathi",
    layout="wide",
)

st.title("Administration Portal")

st.write(
    "Urban planning, civic reports and ward-level priorities."
)

st.subheader("Civic Complaint Management")

st.write(
    "View resident complaints, update their statuses, "
    "and review complaint statistics."
)

if st.button(
    "Manage Civic Reports",
    use_container_width=True,
):
    st.switch_page("pages/manage_reports.py")

st.info(
    "Additional urban planning and ward-level "
    "administration features will be integrated here."
)
