##################################################
# This is the main/entry-point file for the
# RecipeMe application
##################################################

import logging

logging.basicConfig(
    format="%(filename)s:%(lineno)s:%(levelname)s -- %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

import streamlit as st

from modules.nav import SideBarLinks


st.set_page_config(layout="wide")

# Visiting Home.py logs out the current user
st.session_state["authenticated"] = False

SideBarLinks(show_home=True)


# ***************************************************
# Main page
# ***************************************************

logger.info("Loading the Home page of the app")

st.title("RecipeMe")
st.write("#### Hi! As which user would you like to log in?")


# Rachel Green
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


# Mark Smith
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


# Clark Johnson
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


# Existing sample persona
if st.button(
    "Act as John, a Political Strategy Advisor",
    type="primary",
    use_container_width=True,
):
    st.session_state["authenticated"] = True
    st.session_state["role"] = "pol_strat_advisor"
    st.session_state["first_name"] = "John"

    logger.info("Logging in as Political Strategy Advisor Persona")

    st.switch_page("pages/00_Pol_Strat_Home.py")


# Existing sample persona
if st.button(
    "Act as Mohammad, a USAID Worker",
    type="primary",
    use_container_width=True,
):
    st.session_state["authenticated"] = True
    st.session_state["role"] = "usaid_worker"
    st.session_state["first_name"] = "Mohammad"

    st.switch_page("pages/10_USAID_Worker_Home.py")


# Existing sample administrator
if st.button(
    "Act as System Administrator",
    type="primary",
    use_container_width=True,
):
    st.session_state["authenticated"] = True
    st.session_state["role"] = "administrator"
    st.session_state["first_name"] = "SysAdmin"

    st.switch_page("pages/20_Admin_Home.py")