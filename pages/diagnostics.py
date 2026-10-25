
import streamlit as st
import pandas as pd
import numpy as np

from modules.ward_facility_counts import build_ward_facility_counts

st.set_page_config(
    page_title="Ward Diagnostics | UrbanSaathi",
    page_icon="📊",
    layout="wide",
)

if st.button("← Back to Administration"):
    st.switch_page("pages/administration.py")

st.title("📊 Ward Diagnostics")
st.write(
    "Compare mapped public facilities and relative distribution gaps "
    "across Mangaluru's wards."
)

st.warning(
    "The overall score uses an equal-ward facility distribution benchmark, "
    "not population-based service needs. It is an initial comparison metric, "
    "not an official measure of whether a ward is adequately served."
)

CATEGORY_COLUMNS = {
    "Healthcare": "healthcare_count",
    "Education": "education_count",
    "Parks": "parks_count",
    "Bus stops": "transport_count",
}

SCORE_COLUMNS = {
    "Healthcare": "Healthcare Gap Score",
    "Education": "Education Gap Score",
    "Parks": "Parks Gap Score",
    "Bus stops": "Bus stops Gap Score",
}

try:
    with st.spinner("Loading ward facility data..."):
        wards = build_ward_facility_counts().copy()

    required_columns = [
        "KGISWardNo",
        "KGISWardID",
        *CATEGORY_COLUMNS.values(),
    ]

    missing = [
        col for col in required_columns
        if col not in wards.columns
    ]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    wards["_ward_sort"] = pd.to_numeric(
        wards["KGISWardNo"], errors="raise"
    )
    wards = wards.sort_values("_ward_sort").reset_index(drop=True)

    # Validate facility counts.
    for column in CATEGORY_COLUMNS.values():
        wards[column] = pd.to_numeric(
            wards[column], errors="coerce"
        )

        if wards[column].isna().any():
            raise ValueError(
                f"{column} has missing values; scores cannot be "
                "calculated safely."
            )

        if (wards[column] < 0).any():
            raise ValueError(f"{column} contains negative counts.")

    ward_count = len(wards)
    if ward_count == 0:
        raise ValueError("No wards were loaded.")

    # Calculate category gap scores against an equal-ward benchmark.
    for category, count_column in CATEGORY_COLUMNS.items():
        total = float(wards[count_column].sum())
        expected = total / ward_count
        score_column = SCORE_COLUMNS[category]

        if total == 0:
            wards[score_column] = np.nan
        else:
            wards[score_column] = (
                ((expected - wards[count_column]) / expected) * 100
            ).clip(lower=0, upper=100)

    # Equal weighting: 25% for each facility category.
    wards["Overall Priority Score"] = wards[
        list(SCORE_COLUMNS.values())
    ].mean(axis=1, skipna=False)

    if not wards[list(SCORE_COLUMNS.values())].notna().all().all():
        st.warning(
            "At least one facility category has no mapped facilities "
            "citywide. Overall scores may be unavailable."
        )

    st.success(f"Loaded {ward_count} wards.")

    # SECTION 1: Citywide facility totals.
    st.subheader("Citywide Mapped Facility Totals")

    metrics = st.columns(5)
    metrics[0].metric("Wards", ward_count)

    for metric, (category, column) in zip(
        metrics[1:], CATEGORY_COLUMNS.items()
    ):
        metric.metric(category, int(wards[column].sum()))

    st.divider()

    # SECTION 2: Full ward comparison table.
    st.subheader("Ward Facility Comparison Table")

    display_data = wards[
        [
            "KGISWardNo",
            "healthcare_count",
            "education_count",
            "parks_count",
            "transport_count",
            "Overall Priority Score",
        ]
    ].copy()

    display_data = display_data.rename(
        columns={
            "KGISWardNo": "Ward No.",
            "healthcare_count": "Healthcare Count",
            "education_count": "Education Count",
            "parks_count": "Parks Count",
            "transport_count": "Bus Stops Count",
        }
    )

    display_data["Ward No."] = pd.to_numeric(
        display_data["Ward No."], errors="raise"
    )
    display_data = display_data.sort_values("Ward No.")

    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Overall Priority Score": st.column_config.NumberColumn(
                format="%.1f"
            ),
        },
    )

    st.caption(
        "Facility counts are based on mapped records assigned to exactly "
        "one ward. Records outside ward boundaries are excluded, and bus "
        "stations are excluded from the bus-stop metric. Scores do not "
        "account for population, facility capacity, quality, or catchment areas."
    )

    st.divider()

    # SECTION 3: Highest relative distribution gaps.
    st.subheader("Highest Relative Distribution Gaps")

    gap_options = [
        "Overall Priority Score",
        "Healthcare",
        "Education",
        "Parks",
        "Bus stops",
    ]

    selected_gap_metric = st.selectbox(
        "Select facility or overall score",
        gap_options,
        key="diagnostics_gap_metric",
    )

    if selected_gap_metric == "Overall Priority Score":
        selected_score_column = "Overall Priority Score"
    else:
        selected_score_column = SCORE_COLUMNS[selected_gap_metric]

    ranked = wards.dropna(
        subset=[selected_score_column]
    ).sort_values(
        [selected_score_column, "_ward_sort"],
        ascending=[False, True],
    )

    if ranked.empty:
        st.info("No scores are available for this selection.")
    else:
        top = ranked.head(10)

        top_display = top[
            ["KGISWardNo", selected_score_column]
        ].rename(
            columns={
                "KGISWardNo": "Ward No.",
                selected_score_column: "Priority Score",
            }
        )

        top_display["Priority Score"] = (
            top_display["Priority Score"].round(1)
        )

        st.dataframe(
            top_display,
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Showing up to 10 wards with the highest selected priority scores. "
        "Higher scores indicate larger gaps against an equal-ward distribution "
        "benchmark, not a definitive measure of service need."
    )

except Exception as error:
    st.error("Could not load ward diagnostics.")
    st.exception(error)