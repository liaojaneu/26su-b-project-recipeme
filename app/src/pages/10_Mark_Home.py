import logging

import streamlit as st

from modules.nav import SideBarLinks


logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()

first_name = st.session_state.get("first_name", "Mark")

st.title(f"Welcome Professional Chef, {first_name}.")
st.write("### What would you like to do today?")

if st.button("Publish and Manage Recipes", type="primary", use_container_width=True):
    st.switch_page("pages/11_Manage_Recipes.py")

if st.button("View Ingredients and Tags", type="primary", use_container_width=True):
    st.switch_page("pages/12_Ingredients_and_Tags.py")

if st.button("View Recipe Engagement", type="primary", use_container_width=True):
    st.switch_page("pages/13_Recipe_Engagement.py")
