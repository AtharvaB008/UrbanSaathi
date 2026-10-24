from modules.report_service import get_reports
from modules.insight_agent import summarize_reports
import streamlit as st
import pandas as pd
from shapely.geometry import Point
import altair as alt

from modules.data_loader import load_wards
from modules.facilities_map import (
    fetch_facilities,
    classify_facility,
    CATEGORIES,
)


st.set_page_config(
    page_title="UrbanSaathi | Ward Comparison",
    page_icon="🏙️",
    layout="wide",
)

st.title("Neighbourhood Comparison")
st.caption(
    "Compare essential services available in two Mangaluru wards."
)


@st.cache_data(show_spinner="Loading neighbourhood data...")
def get_facility_counts():
    wards = load_wards()
    elements = fetch_facilities()

    category_names = list(CATEGORIES.keys())
    records = []

    for _, ward in wards.iterrows():
        records.append({
            "ward_number": str(
                ward.get("KGISWardNo", ward["KGISWardID"])
            ),
            "geometry": ward.geometry,
            **{category: 0 for category in category_names},
        })

    seen = set()

    for item in elements:
        item_id = (item.get("type"), item.get("id"))

        if item_id in seen:
            continue
        seen.add(item_id)

        tags = item.get("tags", {})
        category = classify_facility(tags)

        if category is None:
            continue

        if "lat" in item and "lon" in item:
            lat, lon = item["lat"], item["lon"]
        elif "center" in item:
            lat = item["center"]["lat"]
            lon = item["center"]["lon"]
        else:
            continue

        point = Point(lon, lat)

        for record in records:
            if record["geometry"].covers(point):
                record[category] += 1
                break

    return pd.DataFrame([
        {
            "Ward": f"Ward {record['ward_number']}",
            **{
                category: record[category]
                for category in category_names
            },
        }
        for record in records
    ])


try:
    data = get_facility_counts()

    if len(data) < 2:
        st.warning("At least two wards are needed for comparison.")
        st.stop()

    ward_names = data["Ward"].tolist()

    col1, col2 = st.columns(2)

    with col1:
        ward_a = st.selectbox(
            "First neighbourhood",
            ward_names,
            index=0,
            key="ward_a",
        )

    with col2:
        ward_b = st.selectbox(
            "Second neighbourhood",
            ward_names,
            index=1,
            key="ward_b",
        )

    if ward_a == ward_b:
        st.info("Choose two different wards to compare them.")
        st.stop()

    first = data.loc[data["Ward"] == ward_a].iloc[0]
    second = data.loc[data["Ward"] == ward_b].iloc[0]

    st.divider()
    st.subheader("Essential services")

    categories = [
        ("Healthcare", "Healthcare facilities"),
        ("Education", "Schools and colleges"),
        ("Parks", "Parks"),
        ("Bus Stops & Stations", "Bus stops and stations"),
    ]

    for category, label in categories:
        st.markdown(f"**{label}**")

        left, right = st.columns(2)

        a = int(first[category])
        b = int(second[category])

        left.metric(ward_a, a)
        right.metric(ward_b, b)

        if a > b:
            st.caption(
                f"{ward_a} has {a - b} more mapped "
                f"{label.lower()} than {ward_b}."
            )
        elif b > a:
            st.caption(
                f"{ward_b} has {b - a} more mapped "
                f"{label.lower()} than {ward_a}."
            )
        else:
            st.caption(
                f"Both wards have the same number of "
                f"mapped {label.lower()}."
            )

    st.divider()
    st.subheader("Compare services at a glance")

    chart_data = (
        data[data["Ward"].isin([ward_a, ward_b])]
        .set_index("Ward")[
            [category for category, _ in categories]
        ]
        .rename(columns={
            "Healthcare": "Healthcare",
            "Education": "Education",
            "Parks": "Parks",
            "Bus Stops & Stations": "Bus stops and stations",
        })
    )

    chart_long = chart_data.reset_index().melt(
        id_vars="Ward",
        var_name="Facility",
        value_name="Count",
    )

    chart = alt.Chart(chart_long).mark_bar().encode(
        x=alt.X("Ward:N", title="Neighbourhood"),
        y=alt.Y("Count:Q", title="Number of facilities"),
        xOffset=alt.XOffset("Facility:N"),
        color=alt.Color(
            "Facility:N",
            scale=alt.Scale(
                domain=[
                    "Healthcare",
                    "Education",
                    "Parks",
                    "Bus stops and stations",
                ],
                range=[
                    "#E45756",
                    "#4C78A8",
                    "#90EE90",
                    "#9467BD",
                ],
            ),
            legend=alt.Legend(title="Facility type"),
        ),
        tooltip=[
            alt.Tooltip("Ward:N", title="Neighbourhood"),
            alt.Tooltip("Facility:N", title="Service"),
            alt.Tooltip("Count:Q", title="Facilities"),
        ],
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)

    st.subheader("What should you know?")

    st.write(
        "These figures show the number of mapped facilities in "
        "each ward. A larger number does not automatically mean "
        "better access: ward population, facility capacity, "
        "condition, and travel distance also matter."
    )

    st.info(
        "Population comparison is not included yet because the "
        "population dataset's units and reference year have not "
        "been verified. We will add meaningful population and "
        "population-density figures once those details are confirmed."
    )

    st.caption(
        "Facility data comes from OpenStreetMap and may be "
        "incomplete or out of date."
    )
    
    st.divider()
    st.header("AI-Assisted Ward Insights")
    st.caption(
        "Evidence-based summaries to help municipal officials "
        "identify patterns and areas for further investigation."
    )

    # Explain facility differences using the counts already displayed.
    
    st.subheader("Service Gaps & Recommended Actions")

    findings = []

    for category, label in categories:
        a = int(first[category])
        b = int(second[category])

        if a == 0 and b == 0:
            title = f"{label}: No mapped facilities in either ward"
            evidence = (
                f"Neither {ward_a} nor {ward_b} has mapped "
                f"{label.lower()} facilities."
            )
            action = (
                "Assess where residents obtain this service, "
                "their travel time, and whether underserved "
                "localities need additional provision."
            )

        elif a == 0 or b == 0:
            lower_ward = ward_a if a == 0 else ward_b
            other_ward = ward_b if a == 0 else ward_a
            other_count = b if a == 0 else a

            title = f"{label}: No mapped facilities in {lower_ward}"
            evidence = (
                f"{lower_ward} has 0 mapped facilities, compared "
                f"with {other_count} in {other_ward}."
            )
            action = (
                "Assess nearby service availability, travel time, "
                "and the population served. If an access gap is "
                "confirmed, evaluate suitable service improvements."
            )

        elif a < b:
            title = f"{label}: Fewer mapped facilities in {ward_a}"
            evidence = (
                f"{ward_a} has {a} facilities, compared with "
                f"{b} in {ward_b}."
            )
            action = (
                "Compare population per facility, travel time, "
                "capacity, and service distribution to determine "
                "whether additional provision is needed."
            )

        elif b < a:
            title = f"{label}: Fewer mapped facilities in {ward_b}"
            evidence = (
                f"{ward_b} has {b} facilities, compared with "
                f"{a} in {ward_a}."
            )
            action = (
                "Compare population per facility, travel time, "
                "capacity, and service distribution to determine "
                "whether additional provision is needed."
            )

        else:
            title = f"{label}: Equal mapped facility counts"
            evidence = (
                f"Both wards have {a} mapped facilities."
            )
            action = (
                "Compare population served, capacity, travel time, "
                "and service quality. Equal counts do not guarantee "
                "equal access."
            )

        findings.append({
            "title": title,
            "evidence": evidence,
            "action": action,
        })

    for finding in findings:
        with st.container(border=True):
            st.markdown(f"**{finding['title']}**")
            st.write(f"**What the data shows:** {finding['evidence']}")
            st.write(f"**Recommended action:** {finding['action']}")

    st.caption(
        "These are preliminary investigation recommendations based "
        "on mapped facility counts, not confirmed service shortages. "
        "Consider verified population, accessibility, facility "
        "capacity, and service quality before making investment decisions."
    )


    # Summarize real civic complaints for the selected wards.
    st.divider()
    st.subheader("Civic complaints in these wards")

    try:
        all_reports = get_reports()

        # Compare report ward IDs with the ward numbers shown in the UI.
        ward_a_id = ward_a.replace("Ward ", "").strip()
        ward_b_id = ward_b.replace("Ward ", "").strip()

        reports_a = [
            report for report in all_reports
            if str(report.get("ward_id", "")).strip() == ward_a_id
        ]
        reports_b = [
            report for report in all_reports
            if str(report.get("ward_id", "")).strip() == ward_b_id
        ]

        report_col_a, report_col_b = st.columns(2)

        for col, ward_name, ward_reports in [
            (report_col_a, ward_a, reports_a),
            (report_col_b, ward_b, reports_b),
        ]:
            with col:
                st.markdown(f"**{ward_name}**")
                result = summarize_reports(ward_reports)

                st.metric("Recorded complaints", result["total_reports"])

                if result["category_counts"]:
                    st.markdown("**Reported issue categories**")
                    for category, count in sorted(
                        result["category_counts"].items(),
                        key=lambda item: item[1],
                        reverse=True,
                    ):
                        st.write(f"- {category}: {count}")

                    if result["recurring_categories"]:
                        st.markdown("**Recurring reported issues**")
                        for category in result["recurring_categories"]:
                            st.write(f"- {category}")
                else:
                    st.write("No complaints are recorded for this ward.")

        st.caption(
            "Complaint totals reflect reports stored in UrbanSaathi, "
            "not the actual prevalence of problems. Confirm that "
            "complaint ward IDs use the same numbering as the map."
        )

    except Exception as report_error:
        st.warning("Civic complaint insights could not be loaded.")
        st.caption(f"Technical details: {report_error}")


except Exception as error:
    st.error("We couldn't load the neighbourhood comparison.")
    st.caption(f"Technical details: {error}")
    st.info(
        "Check that the ward dataset and facility data are "
        "available, then try again."
    )
