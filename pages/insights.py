
import streamlit as st
import pandas as pd

from modules.report_service import get_reports
from modules.insight_agent import summarize_reports


st.set_page_config(
    page_title="UrbanSaathi | Municipal Insights",
    page_icon="🏙️",
    layout="wide",
)
from modules.ui_theme import apply_global_styles

apply_global_styles()

st.title("Municipal Insights")
st.caption(
    "Understand civic complaint patterns using reports submitted "
    "through UrbanSaathi."
)

st.info(
    "These insights summarize recorded civic reports. They describe "
    "reported issues, not independently verified infrastructure "
    "conditions or the full needs of a neighbourhood."
)

try:
    reports = get_reports()

    if not reports:
        st.info(
            "No civic reports have been submitted yet. "
            "Insights will appear here when reports become available."
        )
        st.stop()

    ward_options = ["All wards"] + list(range(1, 61))

    selected_ward = st.selectbox(
        "Choose a ward",
        ward_options,
        format_func=lambda value: (
            value if value == "All wards" else f"Ward {value}"
        ),
    )

    ward_id = (
        None if selected_ward == "All wards"
        else selected_ward
    )

    result = summarize_reports(
        reports,
        ward_id=ward_id,
        period_label="All recorded reports",
    )

    st.divider()
    st.subheader("Complaint overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total reports", result["total_reports"])
    col2.metric(
        "Complaint categories",
        len(result["category_counts"]),
    )
    col3.metric(
        "Statuses represented",
        len(result["status_counts"]),
    )

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Reports by issue category")

        if result["category_counts"]:
            category_data = pd.DataFrame(
                [
                    {"Category": category, "Reports": count}
                    for category, count
                    in result["category_counts"].items()
                ]
            ).sort_values("Reports", ascending=False)

            st.bar_chart(
                category_data.set_index("Category")
            )
        else:
            st.write("No category data is available.")

    with right:
        st.subheader("Reports by status")

        if result["status_counts"]:
            status_data = pd.DataFrame(
                [
                    {"Status": status, "Reports": count}
                    for status, count
                    in result["status_counts"].items()
                ]
            ).sort_values("Reports", ascending=False)

            st.bar_chart(
                status_data.set_index("Status")
            )
        else:
            st.write("No status data is available.")

    st.divider()
    st.subheader("Recurring civic issues")

    recurring = result["recurring_categories"]

    if recurring:
        st.write(
            "These categories appear in at least two reports "
            "within the selected scope:"
        )

        for category in recurring:
            st.markdown(f"- **{category}**")
    else:
        st.write(
            "No category has appeared in two or more reports "
            "within the selected scope yet."
        )

    st.divider()
    st.subheader("Ward distribution")

    if ward_id is None and result["ward_counts"]:
        ward_data = pd.DataFrame(
            [
                {
                    "Ward": (
                        f"Ward {ward}"
                        if ward != "Unknown"
                        else "Unknown ward"
                    ),
                    "Reports": count,
                }
                for ward, count in result["ward_counts"].items()
            ]
        ).sort_values("Reports", ascending=False)

        st.bar_chart(ward_data.set_index("Ward"))
    else:
        st.caption(
            "Select All wards to view the distribution "
            "of reports across wards."
        )

    st.caption(
        "Insights are generated from the civic reports currently "
        "stored in the database. Missing or unreported issues "
        "will not appear in these summaries."
    )

except Exception as error:
    st.error("Unable to load municipal insights.")
    st.caption(f"Technical details: {error}")
