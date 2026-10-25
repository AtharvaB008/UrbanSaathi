
import streamlit as st
import pandas as pd
import altair as alt

from modules.ward_facility_counts import build_ward_facility_counts


st.set_page_config(
    page_title="Ward Comparison | UrbanSaathi",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Ward Comparison")
st.write(
    "Compare essential services across Mangaluru wards, "
    "understand differences between neighbourhoods, and identify "
    "areas that may need further investigation."
)

if st.button("← Back to Administration"):
    st.switch_page("pages/administration.py")


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
    missing = [column for column in required if column not in wards.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if wards.empty:
        raise ValueError("No wards were loaded.")

    # Validate and prepare the shared ward data.
    wards["KGISWardNo"] = wards["KGISWardNo"].astype(str).str.strip()

    for column in CATEGORY_COLUMNS.values():
        wards[column] = pd.to_numeric(wards[column], errors="coerce")

        if wards[column].isna().any() or (wards[column] < 0).any():
            raise ValueError(f"Invalid facility counts in {column}.")

    wards = wards.sort_values(
        "KGISWardNo",
        key=lambda series: pd.to_numeric(series, errors="coerce"),
    ).reset_index(drop=True)

    wards["Ward"] = "Ward " + wards["KGISWardNo"]

    st.subheader("Compare two wards")

    ward_names = wards["Ward"].tolist()

    if len(ward_names) < 2:
        st.warning("At least two wards are needed for comparison.")
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        ward_a = st.selectbox(
            "First ward",
            ward_names,
            index=0,
            key="comparison_ward_a",
        )

    with col2:
        ward_b = st.selectbox(
            "Second ward",
            ward_names,
            index=1,
            key="comparison_ward_b",
        )

    if ward_a == ward_b:
        st.info("Choose two different wards to compare their services.")
        st.stop()

    first = wards.loc[wards["Ward"] == ward_a].iloc[0]
    second = wards.loc[wards["Ward"] == ward_b].iloc[0]

    st.divider()
    st.subheader("Essential services side by side")

    for category, column in CATEGORY_COLUMNS.items():
        left, right = st.columns(2)

        a = int(first[column])
        b = int(second[column])

        with left:
            st.metric(f"{ward_a} · {category}", a)

        with right:
            st.metric(f"{ward_b} · {category}", b)

        if a > b:
            st.caption(
                f"{ward_a} has {a - b} more mapped {category.lower()} "
                f"than {ward_b}."
            )
        elif b > a:
            st.caption(
                f"{ward_b} has {b - a} more mapped {category.lower()} "
                f"than {ward_a}."
            )
        else:
            st.caption(
                f"Both wards have the same number of mapped "
                f"{category.lower()}."
            )

    st.divider()
    st.subheader("📊 Compare all services")

    comparison_data = wards[
        wards["Ward"].isin([ward_a, ward_b])
    ][["Ward", *CATEGORY_COLUMNS.values()]].copy()

    comparison_data = comparison_data.rename(
        columns={
            column: category
            for category, column in CATEGORY_COLUMNS.items()
        }
    )

    chart_long = comparison_data.melt(
        id_vars="Ward",
        var_name="Facility type",
        value_name="Number of facilities",
    )

    chart = (
        alt.Chart(chart_long)
        .mark_bar()
        .encode(
            x=alt.X("Ward:N", title="Ward"),
            y=alt.Y("Number of facilities:Q", title="Mapped facilities"),
            xOffset=alt.XOffset("Facility type:N"),
            color=alt.Color(
                "Facility type:N",
                title="Service type",
            ),
            tooltip=[
                alt.Tooltip("Ward:N", title="Ward"),
                alt.Tooltip("Facility type:N", title="Service"),
                alt.Tooltip(
                    "Number of facilities:Q",
                    title="Facilities",
                ),
            ],
        )
        .properties(height=380)
    )

    st.altair_chart(chart, use_container_width=True)

    st.divider()
    st.subheader("Explore one service across every ward")

    selected_category = st.selectbox(
        "Select a facility type",
        list(CATEGORY_COLUMNS.keys()),
        key="comparison_chart_category",
    )

    count_column = CATEGORY_COLUMNS[selected_category]

    all_wards_chart = wards[["Ward", count_column]].rename(
        columns={count_column: "Number of facilities"}
    )

    st.bar_chart(
        all_wards_chart,
        x="Ward",
        y="Number of facilities",
        use_container_width=True,
    )

    st.divider()
    st.subheader("What should you know?")

    st.write(
        "A ward with fewer mapped facilities may warrant closer "
        "investigation, especially when compared with wards serving "
        "similar populations. These counts alone cannot establish "
        "whether residents have adequate access to services."
    )

    st.info(
        "Population, facility capacity, condition, and travel distance "
        "are not included in this comparison. Population-based conclusions "
        "should wait until the population dataset's units and reference "
        "year are verified."
    )

    st.caption(
        "Facility counts are based on the project's mapped facility data. "
        "Records may be incomplete or out of date."
    )

    st.subheader("🤖 Agentic AI Review")

    st.info(
        "AI-generated investment recommendations can be added here after "
        "the ward population and service-access data have been validated."
    )

except Exception as error:
    st.error("Could not load Ward Comparison.")
    st.caption(f"Technical details: {error}")
