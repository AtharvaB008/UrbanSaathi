
import uuid
from datetime import datetime, timedelta

import streamlit as st
import extra_streamlit_components as stx


def get_resident_id():
    """Return a browser-persistent Resident ID."""

    if "resident_id" in st.session_state:
        return st.session_state["resident_id"]

    cookie_manager = stx.CookieManager(
        key="resident_identity_cookie"
    )
    cookies = cookie_manager.get_all()

    # Wait for the browser cookies to load.
    if cookies is None:
        st.info("Loading your Resident ID...")
        st.stop()

    resident_id = cookies.get("resident_id")

    if not resident_id:
        resident_id = f"US-R-{uuid.uuid4().hex[:8].upper()}"

        cookie_manager.set(
            cookie="resident_id",
            val=resident_id,
            expires_at=datetime.now() + timedelta(days=365),
        )

    st.session_state["resident_id"] = resident_id

    return resident_id
