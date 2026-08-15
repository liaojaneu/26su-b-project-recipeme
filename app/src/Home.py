##################################################
# Main entry-point file for the RecipeMe app
##################################################

import logging

import streamlit as st

from modules.nav import SideBarLinks


# ---------------------------------------------------------------------------
# Logging and page configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    format="%(filename)s:%(lineno)s:%(levelname)s -- %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="RecipeMe",
    page_icon="🍽️",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Reset authentication when visiting the login page
# ---------------------------------------------------------------------------

st.session_state["authenticated"] = False
st.session_state.pop("role", None)
st.session_state.pop("user_id", None)
st.session_state.pop("first_name", None)

SideBarLinks(show_home=True)


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

logger.info("Loading the RecipeMe Home page")

st.title("RecipeMe")
st.write("#### Who would you like to log in as?")

st.write(
    "Select a RecipeMe persona to explore the features available "
    "to that type of user."
)


# ---------------------------------------------------------------------------
# Rachel Green: Home Cook
# ---------------------------------------------------------------------------

if st.button(
    "Act as Rachel Green, a Home Cook",
    type="primary",
    use_container_width=True,
):
    st.session_state["authenticated"] = True
    st.session_state["role"] = "home_cook"
    st.session_state["first_name"] = "Rachel"
    st.session_state["user_id"] = 1

    logger.info("Logging in as Rachel Green")

    st.switch_page("pages/00_Rachel_Home.py")


# ---------------------------------------------------------------------------
# Mark Smith: Professional Chef
# ---------------------------------------------------------------------------

if st.button(
    "Act as Mark Smith, a Professional Chef",
    type="primary",
    use_container_width=True,
):
    st.session_state["authenticated"] = True
    st.session_state["role"] = "chef"
    st.session_state["first_name"] = "Mark"
    st.session_state["user_id"] = 2

    logger.info("Logging in as Mark Smith")

    st.switch_page("pages/10_Mark_Home.py")


# ---------------------------------------------------------------------------
# Clark Johnson: Recipe Content Creator
# ---------------------------------------------------------------------------

if st.button(
    "Act as Clark Johnson, a Recipe Content Creator",
    type="primary",
    use_container_width=True,
):
    st.session_state["authenticated"] = True
    st.session_state["role"] = "creator"
    st.session_state["first_name"] = "Clark"
    st.session_state["user_id"] = 3

    logger.info("Logging in as Clark Johnson")

    st.switch_page("pages/20_Clark_Home.py")


# ---------------------------------------------------------------------------
# David Lopez: System Administrator
# ---------------------------------------------------------------------------

if st.button(
    "Act as David Lopez, a System Administrator",
    type="primary",
    use_container_width=True,
):
    st.session_state["authenticated"] = True
    st.session_state["role"] = "administrator"
    st.session_state["first_name"] = "David"
    st.session_state["user_id"] = 4

    logger.info("Logging in as David Lopez")

    st.switch_page("pages/20_Admin_Home.py")