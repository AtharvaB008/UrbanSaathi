
import streamlit as st
import pandas as pd
import altair as alt

from modules.ward_facility_counts import build_ward_facility_counts
from modules.report_service import get_reports
from modules.insight_agent import (
    summarize_reports,
    explain_ward,
    compare_wards,
)

st.set_page_config(
    page_title="Ward Comparison | UrbanSaathi",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Ward Comparison")
st.write(
    "Compare essential services across Mangaluru wards, "
    "investigate possible service gaps, and review available "
    "civic complaint and AI-assisted insights."
)

if st.button("← Back to Administration"):
    st.switch_page("pages/administration.py")


CATEGORY_COLUMNS = {
    "Healthcare": "healthcare_count",
    "Education": "education_count",
    "Parks": "parks_count",
    "Bus Stops & Stations": "transport_count",
}

CATEGORY_LABELS = {
    "Healthcare": "Healthcare facilities",
    "Education": "Schools and colleges",
    "Parks": "Parks and green spaces",
    "Bus Stops & Stations": "Bus stops and stations",
}

FACILITY_COLORS = {
    "Healthcare": "#E53935",
    "Education": "#1E88E5",
    "Parks": "#43A047",
    "Bus Stops & Stations": "#8E24AA",
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

    wards["KGISWardNo"] = pd.to_numeric(
        wards["KGISWardNo"], errors="coerce"
    )

    wards = wards.dropna(subset=["KGISWardNo"]).copy()

    for column in CATEGORY_COLUMNS.values():
        wards[column] = pd.to_numeric(wards[column], errors="coerce")

        if wards[column].isna().any() or (wards[column] < 0).any():
            raise ValueError(f"Invalid facility counts in {column}.")

    wards = wards.sort_values("KGISWardNo").reset_index(drop=True)
    wards["KGISWardNo"] = wards["KGISWardNo"].astype(int)
    wards["Ward"] = wards["KGISWardNo"].map(lambda number: f"Ward {number}")

    if wards.empty:
        raise ValueError("No valid wards were loaded.")

    # ---------------------------------------------------------
    # Facility distribution across all wards
    # ---------------------------------------------------------
    st.subheader("Facility distribution across wards")

    selected_category = st.selectbox(
        "Explore a facility type across all wards",
        list(CATEGORY_COLUMNS.keys()),
        key="comparison_chart_category",
    )

    count_column = CATEGORY_COLUMNS[selected_category]

    chart_data = wards[["Ward", count_column]].rename(
        columns={count_column: "Number of facilities"}
    )

    st.bar_chart(
        chart_data,
        x="Ward",
        y="Number of facilities",
        use_container_width=True,
    )

    st.caption(
        f"Showing mapped {selected_category.lower()} by ward. "
        "Counts alone do not measure population coverage, accessibility, "
        "facility capacity or service quality."
    )

    st.divider()

    # ---------------------------------------------------------
    # Select and compare two wards
    # ---------------------------------------------------------
    st.subheader("Compare two neighbourhoods")

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
        st.info("Choose two different wards to compare them.")
        st.stop()

    first = wards.loc[wards["Ward"] == ward_a].iloc[0]
    second = wards.loc[wards["Ward"] == ward_b].iloc[0]

    st.subheader("Essential services side by side")

    for category, column in CATEGORY_COLUMNS.items():
        label = CATEGORY_LABELS[category]
        a = int(first[column])
        b = int(second[column])

        left, right = st.columns(2)

        with left:
            st.metric(f"{ward_a} · {label}", a)

        with right:
            st.metric(f"{ward_b} · {label}", b)

        if a > b:
            st.caption(
                f"{ward_a} has {a - b} more mapped {label.lower()} "
                f"than {ward_b}."
            )
        elif b > a:
            st.caption(
                f"{ward_b} has {b - a} more mapped {label.lower()} "
                f"than {ward_a}."
            )
        else:
            st.caption(
                f"Both wards have the same number of mapped "
                f"{label.lower()}."
            )

    # ---------------------------------------------------------
    # Side-by-side comparison chart
    # ---------------------------------------------------------
    st.divider()
    st.subheader("Side-by-side facility chart")

    comparison_data = pd.DataFrame([
        {
            "Ward": ward_a,
            **{
                category: int(first[column])
                for category, column in CATEGORY_COLUMNS.items()
            },
        },
        {
            "Ward": ward_b,
            **{
                category: int(second[column])
                for category, column in CATEGORY_COLUMNS.items()
            },
        },
    ])

    chart_long = comparison_data.melt(
        id_vars="Ward",
        var_name="Facility",
        value_name="Count",
    )

    chart = (
        alt.Chart(chart_long)
        .mark_bar()
        .encode(
            x=alt.X("Ward:N", title="Ward"),
            y=alt.Y("Count:Q", title="Number of mapped facilities"),
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
                alt.Tooltip("Ward:N", title="Ward"),
                alt.Tooltip("Facility:N", title="Facility type"),
                alt.Tooltip("Count:Q", title="Count"),
            ],
        )
        .properties(height=360)
    )

    st.altair_chart(chart, use_container_width=True)

    # ---------------------------------------------------------
    # Service gaps to investigate
    # ---------------------------------------------------------
    st.divider()
    st.subheader("Service gaps to investigate")

    for category, column in CATEGORY_COLUMNS.items():
        label = CATEGORY_LABELS[category]
        a = int(first[column])
        b = int(second[column])

        if a == 0 and b == 0:
            finding = (
                f"Neither ward has mapped {label.lower()}. "
                "Check nearby service availability and resident travel times."
            )
        elif a == 0 or b == 0:
            lower_ward = ward_a if a == 0 else ward_b
            other_ward = ward_b if a == 0 else ward_a
            other_count = b if a == 0 else a

            finding = (
                f"{lower_ward} has no mapped {label.lower()}, while "
                f"{other_ward} has {other_count}. Verify nearby alternatives, "
                "travel times and the population served."
            )
        elif a < b:
            finding = (
                f"{ward_a} has fewer mapped {label.lower()} ({a}) "
                f"than {ward_b} ({b}). Compare population per facility, "
                "accessibility and capacity."
            )
        elif b < a:
            finding = (
                f"{ward_b} has fewer mapped {label.lower()} ({b}) "
                f"than {ward_a} ({a}). Compare population per facility, "
                "accessibility and capacity."
            )
        else:
            finding = (
                f"Both wards have {a} mapped {label.lower()}. "
                "Equal counts do not necessarily mean equal access."
            )

        with st.container(border=True):
            st.markdown(f"**{label}**")
            st.write(finding)

    st.caption(
        "These are preliminary investigation signals, not confirmed "
        "service shortages. Verify population, facility capacity, "
        "travel times and data completeness before making decisions."
    )

    
    st.divider()
    st.header("🤖 AI-Assisted Ward Insights")
    st.caption(
        "Evidence-based explanations for the two selected wards. "
        "Missing scores and benchmarks are reported as unavailable."
    )

    ward_a_data = {
        "ward_id": str(int(first["KGISWardNo"])),
        "ward_name": ward_a,
        "priority": {"score": None, "components": []},
        "facilities": {
            category: {
                "actual_count": int(first[column]),
                "benchmark_count": None,
                "source": "Mapped ward facility counts",
            }
            for category, column in CATEGORY_COLUMNS.items()
        },
        "missing_data": [
            "Verified population and population density",
            "Validated facility benchmarks",
            "Official ward priority score",
        ],
    }

    ward_b_data = {
        "ward_id": str(int(second["KGISWardNo"])),
        "ward_name": ward_b,
        "priority": {"score": None, "components": []},
        "facilities": {
            category: {
                "actual_count": int(second[column]),
                "benchmark_count": None,
                "source": "Mapped ward facility counts",
            }
            for category, column in CATEGORY_COLUMNS.items()
        },
        "missing_data": [
            "Verified population and population density",
            "Validated facility benchmarks",
            "Official ward priority score",
        ],
    }

    insights = compare_wards(ward_a_data, ward_b_data)

    st.subheader("Ward comparison summary")
    st.write(insights["score_comparison"])
    st.info(
        "Official priority scores are not available in this comparison "
        "dataset. The following findings use observed facility counts "
        "rather than estimated priority scores."
    )

    for ward_insight in (insights["ward_a"], insights["ward_b"]):
        with st.container(border=True):
            st.markdown(f"### {ward_insight['ward_name']}")
            st.write(ward_insight["summary"])

            st.markdown("**Facility findings**")
            for finding in ward_insight["facility_findings"]:
                actual = finding["actual_count"]
                benchmark = finding["benchmark_count"]

                if benchmark is None:
                    st.write(
                        f"- **{finding['category']}:** {actual} mapped "
                        "facilities; benchmark unavailable."
                    )
                else:
                    st.write(
                        f"- **{finding['category']}:** {actual} mapped "
                        f"facilities against a benchmark of {benchmark}."
                    )

            if ward_insight["warnings"]:
                st.markdown("**Data limitations**")
                for warning in ward_insight["warnings"]:
                    st.write(f"- {warning}")

            if ward_insight["investigations"]:
                st.markdown("**Recommended investigations**")
                for recommendation in ward_insight["investigations"]:
                    st.write(f"- {recommendation}")

    st.caption(insights["ward_a"]["disclaimer"])


    # ---------------------------------------------------------
    # Civic complaints in selected wards
    # ---------------------------------------------------------
    st.divider()
    st.subheader("Civic complaints in these wards")

    try:
        all_reports = get_reports()

        ward_a_id = str(int(first["KGISWardNo"]))
        ward_b_id = str(int(second["KGISWardNo"]))

        reports_a = [
            report for report in all_reports
            if str(report.get("ward_id", "")).strip() == ward_a_id
        ]
        reports_b = [
            report for report in all_reports
            if str(report.get("ward_id", "")).strip() == ward_b_id
        ]

        report_col_a, report_col_b = st.columns(2)

        for column_ui, ward_name, ward_reports in [
            (report_col_a, ward_a, reports_a),
            (report_col_b, ward_b, reports_b),
        ]:
            with column_ui:
                st.markdown(f"**{ward_name}**")
                result = summarize_reports(ward_reports)

                st.metric(
                    "Recorded complaints",
                    result["total_reports"],
                )

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
            "not the actual prevalence of problems. Verify that complaint "
            "ward IDs use the same numbering as the ward dataset."
        )

    except Exception as report_error:
        st.warning("Civic complaint insights could not be loaded.")
        st.caption(f"Technical details: {report_error}")

except Exception as error:
    st.error("Could not load Ward Comparison.")
    st.exception(error)
