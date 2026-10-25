
import streamlit as st


def apply_global_styles():
    st.markdown(
        """
        <style>
            /* Hide Streamlit's built-in sidebar and page navigation */
            [data-testid="stSidebar"] {
                display: none !important;
            }

            /* Hide the black top header and toolbar */
            [data-testid="stHeader"],
            [data-testid="stToolbar"],
            [data-testid="stDecoration"] {
                display: none !important;
            }

            /* Remove sidebar spacing and use the available width */
            [data-testid="stAppViewContainer"] > .main {
                margin-left: 0 !important;
            }

            [data-testid="stMainBlockContainer"],
            .block-container {
                max-width: 100% !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
