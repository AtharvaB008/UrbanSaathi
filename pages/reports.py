
import streamlit as st
from pathlib import Path
import sys

# Allow imports from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure the page before other Streamlit commands.
st.set_page_config(
    page_title="Civic Reports | UrbanSaathi",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from database.init_db import init_database
from modules.photo_service import save_complaint_photo
from modules.resident_identity import get_resident_id
from modules.report_service import (
    REPORT_CATEGORIES,
    submit_report,
    get_report_by_id,
    get_report_history,
)

# Initialize the database and retrieve the resident's ID.
init_database()
resident_id = get_resident_id()

st.title("Civic Reports")
st.write("Report civic issues in your neighbourhood.")

st.info(f"Your Resident ID: {resident_id}")

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
        placeholder="e.g., Broken streetlight near the park",
    )

    category = st.selectbox(
        "Complaint Category *",
        REPORT_CATEGORIES,
    )

    ward_id = st.selectbox(
        "Ward Number *",
        options=list(range(1, 61)),
    )

    locality = st.text_input(
        "Locality / Area Name *",
        placeholder="e.g., Hampankatta",
    )

    location_details = st.text_input(
        "Exact Location / Nearby Landmark *",
        placeholder="e.g., Near the main bus stop",
    )

    description = st.text_area(
        "Describe the Issue *",
        placeholder="Explain the problem in detail...",
        height=130,
    )

    uploaded_photo = st.file_uploader(
        "Attach a Photo (Optional)",
        type=["jpg", "jpeg", "png", "webp"],
        help="Upload a photo of the civic issue (maximum 5 MB).",
    )

    submitted = st.form_submit_button(
        "Submit Complaint",
        type="primary",
        use_container_width=True,
    )

if submitted:
    photo_path = None
    report_id = None

    try:
        if uploaded_photo is not None:
            photo_path = save_complaint_photo(uploaded_photo)

        report_id = submit_report(
            title=title,
            category=category,
            description=description,
            ward_id=ward_id,
            locality=locality,
            location_details=location_details,
            photo_path=photo_path,
            resident_id=resident_id,
        )

        st.success(
            f"Complaint submitted successfully! "
            f"Your Report ID is #{report_id}."
        )

        st.info(
            f"Your Resident ID is {resident_id}. "
            "Save your Report ID to check your complaint status."
        )

    except ValueError as error:
        st.error(str(error))

    except Exception as error:
        st.error(
            "Unable to submit the complaint right now. "
            "Please try again."
        )
        # Print details in the terminal for debugging.
        print(f"Complaint submission error: {error}")

    finally:
        if photo_path is not None and report_id is None:
            (PROJECT_ROOT / photo_path).unlink(missing_ok=True)

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
        value=1,
    )

    track_clicked = st.form_submit_button(
        "Check Status",
        use_container_width=True,
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
                    st.markdown(f"**{entry['new_status']}**")
                    st.caption(f"Updated: {entry['changed_at']}")

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

    except Exception as error:
        st.error(
            "Unable to retrieve the complaint right now. "
            "Please try again."
        )
        print(f"Complaint tracking error: {error}")
