
import streamlit as st
import pandas as pd

from modules.ward_facility_counts import build_ward_facility_counts

st.set_page_config(
    page_title="Ward Comparison | UrbanSaathi",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Ward Comparison")
st.write(
    "Compare facility distribution across Mangaluru wards "
    "to understand how essential services are distributed."
)

if st.button("← Back to Administration"):
    st.switch_page("pages/administration.py")

st.divider()

CATEGORY_COLUMNS = {
    "Healthcare": "healthcare_count",
    "Education": "education_count",
    "Parks": "parks_count",
    "Bus stops": "transport_count",
}

try:
    with st.spinner("Loading ward facility data..."):
        wards = build_ward_facility_counts().copy()

    required = ["KGISWardNo", *CATEGORY_COLUMNS.values()]
    missing = [col for col in required if col not in wards.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    wards["_ward_sort"] = pd.to_numeric(
        wards["KGISWardNo"], errors="raise"
    )

    for column in CATEGORY_COLUMNS.values():
        wards[column] = pd.to_numeric(
            wards[column], errors="coerce"
        )

        if wards[column].isna().any() or (wards[column] < 0).any():
            raise ValueError(
                f"Invalid facility counts in {column}."
            )

    wards = wards.sort_values(
        "_ward_sort"
    ).reset_index(drop=True)

    if wards.empty:
        raise ValueError("No wards were loaded.")

    # Independent controls for the Ward Comparison chart.
    st.subheader("📊 Ward Facility Comparison")

    selected_category = st.selectbox(
        "Select a facility to compare",
        list(CATEGORY_COLUMNS.keys()),
        key="comparison_chart_category",
    )

    count_column = CATEGORY_COLUMNS[selected_category]

    chart_data = wards[
        ["KGISWardNo", count_column]
    ].copy()

    chart_data["KGISWardNo"] = (
        "Ward " + chart_data["KGISWardNo"].astype(str)
    )

    chart_data = chart_data.rename(
        columns={
            "KGISWardNo": "Ward",
            count_column: "Number of facilities",
        }
    )

    st.bar_chart(
        chart_data,
        x="Ward",
        y="Number of facilities",
        use_container_width=True,
    )

    st.caption(
        f"Showing the number of {selected_category.lower()} "
        "facilities recorded in each ward. Counts alone do not "
        "account for population, accessibility, or service capacity."
    )

    st.divider()

    st.subheader("🤖 Agentic AI Review")
    st.info(
        "Reserved for future development. The AI review can "
        "later interpret ward comparisons and highlight areas "
        "that may warrant further investigation."
    )

except Exception as error:
    st.error("Could not load Ward Comparison.")
    st.exception(error)
