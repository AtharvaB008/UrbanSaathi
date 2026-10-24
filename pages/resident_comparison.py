
import streamlit as st
import pandas as pd
import altair as alt

from modules.ward_facility_counts import build_ward_facility_counts


st.set_page_config(
    page_title="Neighbourhood Comparison | UrbanSaathi",
    page_icon="🏘️",
    layout="wide",
)

st.title("🏘️ Neighbourhood Comparison")
st.write(
    "Explore mapped facilities in two Mangaluru neighbourhoods. "
    "Use this comparison to understand local amenities and questions "
    "you may want to investigate."
)

if st.button("← Back to Resident Portal"):
    st.switch_page("pages/resident.py")


CATEGORY_COLUMNS = {
    "Healthcare": "healthcare_count",
    "Schools and colleges": "education_count",
    "Parks and green spaces": "parks_count",
    "Bus stops and stations": "transport_count",
}

# Consistent facility colours across UrbanSaathi.
FACILITY_COLORS = {
    "Healthcare": "#E53935",
    "Schools and colleges": "#1E88E5",
    "Parks and green spaces": "#43A047",
    "Bus stops and stations": "#8E24AA",
}


try:
    with st.spinner("Loading neighbourhood information..."):
        wards = build_ward_facility_counts().copy()

    required = ["KGISWardNo", *CATEGORY_COLUMNS.values()]
    missing = [
        column for column in required
        if column not in wards.columns
    ]

    if missing:
        st.error(
            f"Required neighbourhood data is unavailable: {missing}"
        )
        st.stop()

    wards["KGISWardNo"] = pd.to_numeric(
        wards["KGISWardNo"],
        errors="coerce",
    )

    for column in CATEGORY_COLUMNS.values():
        wards[column] = pd.to_numeric(
            wards[column],
            errors="coerce",
        )

    wards = wards.dropna(subset=["KGISWardNo"])

    if wards.empty:
        st.warning("No neighbourhood data is currently available.")
        st.stop()

    invalid_counts = any(
        wards[column].isna().any()
        or (wards[column] < 0).any()
        for column in CATEGORY_COLUMNS.values()
    )

    if invalid_counts:
        st.error(
            "Some facility counts are invalid. Please check the data."
        )
        st.stop()

    wards = wards.sort_values(
        "KGISWardNo"
    ).reset_index(drop=True)

    wards["Ward"] = wards["KGISWardNo"].astype(int).map(
        lambda number: f"Ward {number}"
    )

    ward_names = wards["Ward"].tolist()

    if len(ward_names) < 2:
        st.info(
            "At least two neighbourhoods are needed for comparison."
        )
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        ward_a = st.selectbox(
            "Choose your neighbourhood",
            ward_names,
            index=0,
        )

    with col2:
        ward_b = st.selectbox(
            "Choose another neighbourhood",
            ward_names,
            index=1,
        )

    if ward_a == ward_b:
        st.info("Please choose two different neighbourhoods.")
        st.stop()

    first = wards.loc[wards["Ward"] == ward_a].iloc[0]
    second = wards.loc[wards["Ward"] == ward_b].iloc[0]

    # --------------------------------------------------
    # Neighbourhood facility overview
    # --------------------------------------------------
    st.divider()
    st.subheader("Your neighbourhoods at a glance")

    left, right = st.columns(2)

    for ui_column, ward_name, row in [
        (left, ward_a, first),
        (right, ward_b, second),
    ]:
        with ui_column:
            st.markdown(f"### {ward_name}")

            for category, column in CATEGORY_COLUMNS.items():
                st.metric(
                    label=category,
                    value=int(row[column]),
                )

    # --------------------------------------------------
    # Coloured comparison chart
    # --------------------------------------------------
    st.divider()
    st.subheader("Compare local amenities")

    chart_data = pd.DataFrame([
        {
            "Neighbourhood": ward_a,
            **{
                category: int(first[column])
                for category, column in CATEGORY_COLUMNS.items()
            },
        },
        {
            "Neighbourhood": ward_b,
            **{
                category: int(second[column])
                for category, column in CATEGORY_COLUMNS.items()
            },
        },
    ])

    chart_long = chart_data.melt(
        id_vars="Neighbourhood",
        var_name="Facility",
        value_name="Count",
    )

    chart = (
        alt.Chart(chart_long)
        .mark_bar()
        .encode(
            x=alt.X(
                "Neighbourhood:N",
                title="Neighbourhood",
            ),
            y=alt.Y(
                "Count:Q",
                title="Number of mapped facilities",
            ),
            xOffset=alt.XOffset("Facility:N"),
            color=alt.Color(
                "Facility:N",
                title="Facility type",
                scale=alt.Scale(
                    domain=list(FACILITY_COLORS.keys()),
                    range=list(FACILITY_COLORS.values()),
                ),
            ),
            tooltip=[
                "Neighbourhood",
                "Facility",
                "Count",
            ],
        )
        .properties(height=360)
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )

    # --------------------------------------------------
    # Plain-language comparison insights
    # --------------------------------------------------
    st.divider()
    st.subheader("What does this comparison tell you?")

    for category, column in CATEGORY_COLUMNS.items():
        count_a = int(first[column])
        count_b = int(second[column])

        if count_a > count_b:
            st.write(
                f"- **{category}:** {ward_a} has "
                f"{count_a - count_b} more mapped facilities "
                f"than {ward_b}."
            )

        elif count_b > count_a:
            st.write(
                f"- **{category}:** {ward_b} has "
                f"{count_b - count_a} more mapped facilities "
                f"than {ward_a}."
            )

        else:
            st.write(
                f"- **{category}:** Both neighbourhoods have "
                f"{count_a} mapped facilities."
            )

    st.info(
        "More mapped facilities do not automatically mean better access. "
        "Population, opening hours, capacity, distance and travel times "
        "also matter. These counts are a starting point for exploration, "
        "not a complete measure of neighbourhood quality."
    )

except Exception:
    st.error("Could not load neighbourhood comparison.")
    st.exception(Exception)


st.caption("UrbanSaathi · Mangaluru, Karnataka")
