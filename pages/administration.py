import streamlit as st

st.set_page_config(page_title="Administration | UrbanSaathi", layout="wide")

if st.button("← Back to Home"):
    st.switch_page("app.py")

st.title("🏛️ Administration Portal")
st.write("Urban planning, civic reports and ward-level priorities.")
st.info("Administration module integration will follow.")