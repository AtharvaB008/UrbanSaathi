
import streamlit as st


from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.init_db import init_database
from modules.report_service import (
    REPORT_CATEGORIES,
    submit_report,
    get_report_by_id,
    get_report_history,
)

init_database()


st.set_page_config(
    page_title="Civic Reports | UrbanSaathi",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Civic Reports")
st.write("Report civic issues in your neighbourhood.")

st.info(
    "Complaint submission and status tracking "
    "will be connected here."
)

if st.button("← Back to Resident Portal"):
    st.switch_page("pages/resident.py")



st.divider()

st.subheader("Report a Civic Issue")

st.write(
    "Tell us about a problem in your neighbourhood. "
    "Your report will be recorded for administrative review."
)

with st.form("civic_report_form", clear_on_submit=True):

    title = st.text_input(
        "Complaint Title *",
        placeholder="e.g., Broken streetlight near the park"
    )

    category = st.selectbox(
        "Complaint Category *",
        REPORT_CATEGORIES
    )

    ward_id = st.selectbox(
        "Ward Number *",
        options=list(range(1, 61))
    )

    locality = st.text_input(
        "Locality / Area Name *",
        placeholder="e.g., Hampankatta"
    )

    location_details = st.text_input(
        "Exact Location / Nearby Landmark *",
        placeholder="e.g., Near the main bus stop"
    )

    description = st.text_area(
        "Describe the Issue *",
        placeholder="Explain the problem in detail...",
        height=130
    )

    submitted = st.form_submit_button(
        "Submit Complaint",
        type="primary",
        use_container_width=True
    )

if submitted:
    try:
        report_id = submit_report(
            title=title,
            category=category,
            description=description,
            ward_id=ward_id,
            locality=locality,
            location_details=location_details
        )

        st.success(
            f"Complaint submitted successfully! "
            f"Your Report ID is #{report_id}."
        )

        st.info(
            "Save your Report ID. You will need it "
            "to check the status of your complaint."
        )

    except ValueError as error:
        st.error(str(error))

    except Exception:
        st.error(
            "Unable to submit the complaint right now. "
            "Please try again."
        )



st.divider()

st.subheader("Track Your Complaint")

st.write(
    "Enter your Report ID to check the current "
    "status of your complaint."
)

with st.form("track_complaint_form"):
    tracking_id = st.number_input(
        "Report ID",
        min_value=1,
        step=1,
        value=1
    )

    track_clicked = st.form_submit_button(
        "Check Status",
        use_container_width=True
    )

if track_clicked:
    try:
        report = get_report_by_id(int(tracking_id))

        if report is None:
            st.warning(
                "No complaint was found with this Report ID."
            )
        else:
            st.success("Complaint found!")

            st.write("**Report ID:**", report["report_id"])
            st.write("**Title:**", report["title"])
            st.write("**Category:**", report["category"])
            st.write("**Ward:**", report["ward_id"])
            st.write("**Status:**", report["status"])


            st.markdown("### Complaint Progress")

            history = get_report_history(report["report_id"])

            if not history:
                st.info("No status history is available.")
            else:
                
                for entry in history:
                    st.markdown(
                        f"**{entry['new_status']}**"
                    )

                    st.caption(
                        f"Updated: {entry['changed_at']}"
                    )

                    if entry["admin_note"]:
                        if entry["new_status"] == "Rejected / Invalid":
                            st.warning(
                                "Reason for Rejection: "
                                + entry["admin_note"]
                            )
                        else:
                            st.info(
                                "Administrative Update: "
                                + entry["admin_note"]
                            )

                    st.divider()



    except ValueError as error:
        st.error(str(error))

    except Exception:
        st.error(
            "Unable to retrieve the complaint right now."
        )
