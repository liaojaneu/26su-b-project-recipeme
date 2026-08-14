import logging

import streamlit as st

from modules.nav import SideBarLinks


logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()

first_name = st.session_state.get("first_name", "Rachel")

st.title(f"Welcome Home Cook, {first_name}.")
st.write("### What would you like to do today?")

if st.button("Discover Recipes", type="primary", use_container_width=True):
    st.switch_page("pages/01_Discover_Recipes.py")

if st.button("Manage My Collections", type="primary", use_container_width=True):
    st.switch_page("pages/02_My_Collections.py")

if st.button("Reviews and Creators", type="primary", use_container_width=True):
    st.switch_page("pages/03_Reviews_and_Creators.py")

