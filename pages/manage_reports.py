
import streamlit as st
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.init_db import init_database
from modules.report_service import (
    REPORT_CATEGORIES,
    get_reports,
    get_report_by_id,
    get_report_counts,
    get_report_history,
    update_report_status,
)

from modules.investigation_priority import (
    get_live_investigation_recommendations,
    explain_investigation_priority,
)

init_database()

st.set_page_config(
    page_title="Manage Civic Reports | UrbanSaathi",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Manage Civic Reports")
st.write(
    "Administration dashboard for viewing and managing "
    "resident civic complaints."
)


st.divider()

st.subheader("Complaint Overview")

try:
    counts = get_report_counts()

    total_col, submitted_col, review_col = st.columns(3)

    with total_col:
        st.metric("Total Complaints", counts["Total"])

    with submitted_col:
        st.metric("Submitted", counts["Submitted"])

    with review_col:
        st.metric("Under Review", counts["Under Review"])

    progress_col, resolved_col, rejected_col = st.columns(3)

    with progress_col:
        st.metric("In Progress", counts["In Progress"])

    with resolved_col:
        st.metric("Resolved", counts["Resolved"])

    with rejected_col:
        st.metric(
            "Rejected / Invalid",
            counts["Rejected / Invalid"]
        )

except Exception:
    st.error("Unable to load complaint statistics.")


st.divider()

# -----------------------------------------
# Investigation Priority Recommendations
# -----------------------------------------

st.subheader("Investigation Priority Recommendations")

st.caption(
    "Rule-based recommendations using complaint category, "
    "potential duplicate reports, and complaint age. "
    "These are advisory scores, not confirmed emergencies "
    "or official municipal decisions."
)

try:
    recommendations = get_live_investigation_recommendations()

    if not recommendations:
        st.info(
            "No active complaints are available for "
            "investigation-priority analysis."
        )
    else:
        recommendation_rows = []

        for item in recommendations:
            recommendation_rows.append({
                "Report ID": item["report_id"],
                "Related Reports": item["related_complaint_count"],
                "Priority Score": item["priority_score"],
                "Recommended Priority": item["priority_level"],
            })

        st.dataframe(
            recommendation_rows,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Understand the Recommendation")

        recommendation_options = {
            f"Complaint #{item['report_id']} — {item['priority_level']} Priority":
            item
            for item in recommendations
        }

        selected_recommendation_label = st.selectbox(
            "Select a complaint to view its investigation priority explanation",
            options=list(recommendation_options.keys()),
            key="priority_explanation_selector",
        )

        selected_recommendation = recommendation_options[
            selected_recommendation_label
        ]

        with st.expander(
            "View Investigation Priority Explanation",
            expanded=False,
        ):
            st.write(
                explain_investigation_priority(
                    selected_recommendation
                )
            )

            st.caption(
                "This recommendation is generated using "
                "transparent Python scoring rules. "
                "It does not automatically change complaint "
                "status or replace administrator judgment."
            )

        st.info(
            "Potential duplicates are identified using textual "
            "and location similarity. An administrator should "
            "verify matches before deciding what to investigate."
        )

except Exception:
    st.error(
        "Unable to load investigation recommendations. "
        "Please check the complaint intelligence modules."
    )


st.divider()


st.subheader("All Civic Complaints")

st.write(
    "Filter and review complaints submitted by residents "
    "across Mangaluru."
)

# Complaint filters
ward_col, category_col, status_col = st.columns(3)

with ward_col:
    selected_ward = st.selectbox(
        "Filter by Ward",
        options=["All Wards"] + list(range(1, 61))
    )

with category_col:
    selected_category = st.selectbox(
        "Filter by Category",
        options=["All Categories"] + list(REPORT_CATEGORIES)
    )

with status_col:
    selected_status = st.selectbox(
        "Filter by Status",
        options=[
            "All Statuses",
            "Submitted",
            "Under Review",
            "In Progress",
            "Resolved",
            "Rejected / Invalid",
        ]
    )

# Convert "All" selections into None
ward_filter = (
    None if selected_ward == "All Wards"
    else selected_ward
)

category_filter = (
    None if selected_category == "All Categories"
    else selected_category
)

status_filter = (
    None if selected_status == "All Statuses"
    else selected_status
)

try:
    reports = get_reports(
        ward_id=ward_filter,
        category=category_filter,
        status=status_filter,
    )


    if not reports:
        st.info("No civic complaints have been submitted yet.")

    else:
        table_data = []

        for report in reports:
            table_data.append({
                "Report ID": report["report_id"],
                "Title": report["title"],
                "Category": report["category"],
                "Ward": report["ward_id"],
                "Locality": report["locality"],
                "Status": report["status"],
                "Submitted At": report["created_at"],
            })

        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            f"Displaying {len(reports)} civic complaint(s)."
        )

except Exception:
    st.error("Unable to load civic complaints.")


st.divider()

st.subheader("Manage Individual Complaint")

st.write(
    "Select a complaint to review its details and manage its status."
)

try:
    all_reports = get_reports()

    if not all_reports:
        st.info("No complaints are available for management.")

    else:
        report_options = {
            f"#{report['report_id']} - {report['title']}": report["report_id"]
            for report in all_reports
        }

        selected_report_label = st.selectbox(
            "Select a Complaint",
            options=list(report_options.keys()),
            key="manage_report_selection"
        )

        selected_report_id = report_options[selected_report_label]

        selected_report = get_report_by_id(selected_report_id)

        if selected_report:
            st.write("**Report ID:**", selected_report["report_id"])
            st.write("**Title:**", selected_report["title"])
            st.write("**Category:**", selected_report["category"])
            st.write("**Ward:**", selected_report["ward_id"])
            st.write("**Locality:**", selected_report["locality"])
            st.write(
                "**Location Details:**",
                selected_report["location_details"]
            )
            st.write(
                "**Description:**",
                selected_report["description"]
            )

            st.markdown("### Attached Photo")

            photo_path = selected_report["photo_path"]

            if photo_path:
                from modules.photo_service import UPLOAD_DIR

                photo_file = (PROJECT_ROOT / photo_path).resolve()

                if (
                    photo_file.parent == UPLOAD_DIR.resolve()
                    and photo_file.is_file()
                    and photo_file.suffix.lower()
                    in (".jpg", ".png", ".webp")
                ):
                    st.image(
                        str(photo_file),
                        caption="Photo submitted with this complaint",
                        width=450,
                    )
                else:
                    st.warning(
                        "The attached photo could not be found."
                    )
            else:
                st.info("No photo was attached to this complaint.")


            st.write(
                "**Current Status:**",
                selected_report["status"]
            )

            st.markdown("### Complaint Status History")

            report_history = get_report_history(
                selected_report_id
            )

            if not report_history:
                st.info("No status history is available.")

            else:
                for entry in report_history:
                    st.write(
                        "**Status:**",
                        entry["new_status"]
                    )

                    st.caption(
                        f"Updated: {entry['changed_at']}"
                    )

                    if entry["admin_note"]:
                        if entry["new_status"] == "Rejected / Invalid":
                            st.error(
                                "Reason for Rejection: "
                                + entry["admin_note"]
                            )
                        else:
                            st.info(
                                "Administrative Note: "
                                + entry["admin_note"]
                            )

                    st.divider()


            st.markdown("### Update Complaint Status")

            status_options = [
                "Under Review",
                "In Progress",
                "Resolved",
                "Rejected / Invalid",
            ]

            available_statuses = [
                status
                for status in status_options
                if status != selected_report["status"]
            ]

            with st.form(
                f"update_status_form_{selected_report_id}"
            ):
                new_status = st.selectbox(
                    "New Status",
                    options=available_statuses
                )


                if new_status == "Rejected / Invalid":
                    note_label = "Reason for Rejection *"
                    note_placeholder = (
                        "Explain why this complaint is being rejected..."
                    )
                else:
                    note_label = "Administrative Note"
                    note_placeholder = "Explain the status update..."

                admin_note = st.text_area(
                    note_label,
                    placeholder=note_placeholder,
                )

                update_clicked = st.form_submit_button(
                    "Update Status",
                    type="primary",
                    use_container_width=True
                )

            if update_clicked:
                try:
                    update_report_status(
                        report_id=selected_report_id,
                        new_status=new_status,
                        admin_note=admin_note
                    )

                    st.success(
                        f"Complaint #{selected_report_id} "
                        f"updated to {new_status}."
                    )

                    st.rerun()

                except ValueError as error:
                    st.error(str(error))

                except Exception:
                    st.error(
                        "Unable to update the complaint status."
                    )


except Exception:
    st.error("Unable to load complaint details.")


if st.button("← Back to Administration Portal"):
    st.switch_page("pages/administration.py")
