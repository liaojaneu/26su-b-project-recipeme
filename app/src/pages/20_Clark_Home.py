import logging

import streamlit as st

from modules.nav import SideBarLinks


logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()

first_name = st.session_state.get("first_name", "Clark")

st.title(f"Welcome Recipe Content Creator, {first_name}.")
st.write("### What would you like to do today?")

if st.button("Manage Creator Content", type="primary", use_container_width=True):
    st.switch_page("pages/21_Creator_Content.py")

if st.button("Audience Reviews and Replies", type="primary", use_container_width=True):
    st.switch_page("pages/22_Audience_Reviews.py")

if st.button("Manage Themed Collections", type="primary", use_container_width=True):
    st.switch_page("pages/23_Themed_Collections.py")
