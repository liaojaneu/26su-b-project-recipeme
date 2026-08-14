# Idea borrowed from:
# https://github.com/fsmosca/sample-streamlit-authenticator

# This file has functions to add links to the left sidebar
# based on the user's role.

import streamlit as st


# ---- General ----------------------------------------------------------------

def home_nav():
    st.sidebar.page_link(
        "Home.py",
        label="Home",
        icon="🏠",
    )


def about_page_nav():
    st.sidebar.page_link(
        "pages/30_About.py",
        label="About",
        icon="🧠",
    )


# ---- RecipeMe: Rachel --------------------------------------------------------

def rachel_home_nav():
    st.sidebar.page_link(
        "pages/00_Rachel_Home.py",
        label="Rachel Home",
        icon="🏠",
    )


# ---- RecipeMe: Mark ----------------------------------------------------------

def mark_home_nav():
    st.sidebar.page_link(
        "pages/10_Mark_Home.py",
        label="Mark Home",
        icon="🏠",
    )


def recipe_engagement_nav():
    st.sidebar.page_link(
        "pages/13_Recipe_Engagement.py",
        label="Recipe Engagement",
        icon="📊",
    )


# ---- RecipeMe: Clark ---------------------------------------------------------

def clark_home_nav():
    st.sidebar.page_link(
        "pages/20_Clark_Home.py",
        label="Clark Home",
        icon="🏠",
    )


# ---- Role: pol_strat_advisor ------------------------------------------------

def pol_strat_home_nav():
    st.sidebar.page_link(
        "pages/00_Pol_Strat_Home.py",
        label="Political Strategist Home",
        icon="👤",
    )


def world_bank_viz_nav():
    st.sidebar.page_link(
        "pages/01_World_Bank_Viz.py",
        label="World Bank Visualization",
        icon="🏦",
    )


def map_demo_nav():
    st.sidebar.page_link(
        "pages/02_Map_Demo.py",
        label="Map Demonstration",
        icon="🗺️",
    )


# ---- Role: usaid_worker -----------------------------------------------------

def usaid_worker_home_nav():
    st.sidebar.page_link(
        "pages/10_USAID_Worker_Home.py",
        label="USAID Worker Home",
        icon="🏠",
    )


def ngo_directory_nav():
    st.sidebar.page_link(
        "pages/14_NGO_Directory.py",
        label="NGO Directory",
        icon="📁",
    )


def add_ngo_nav():
    st.sidebar.page_link(
        "pages/15_Add_NGO.py",
        label="Add New NGO",
        icon="➕",
    )


def prediction_nav():
    st.sidebar.page_link(
        "pages/11_Prediction.py",
        label="Regression Prediction",
        icon="📈",
    )


def api_test_nav():
    st.sidebar.page_link(
        "pages/12_API_Test.py",
        label="Test the API",
        icon="🛜",
    )


def classification_nav():
    st.sidebar.page_link(
        "pages/13_Classification.py",
        label="Classification Demo",
        icon="🌺",
    )


# ---- Role: administrator ----------------------------------------------------

def admin_home_nav():
    st.sidebar.page_link(
        "pages/20_Admin_Home.py",
        label="System Admin",
        icon="🖥️",
    )


def ml_model_mgmt_nav():
    st.sidebar.page_link(
        "pages/21_ML_Model_Mgmt.py",
        label="ML Model Management",
        icon="🏢",
    )


# ---- Sidebar assembly -------------------------------------------------------

def SideBarLinks(show_home=False):
    """
    Renders sidebar navigation links based on the logged-in user's role.
    """

    st.sidebar.image(
        "assets/recipeme_logo.png",
        width=200,
    )

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"] and not show_home:
        st.switch_page("Home.py")

    if show_home:
        home_nav()

    if st.session_state["authenticated"]:
        role = st.session_state.get("role")

        if role == "home_cook":
            rachel_home_nav()

        if role == "chef":
            mark_home_nav()
            recipe_engagement_nav()

        if role == "creator":
            clark_home_nav()

        if role == "pol_strat_advisor":
            pol_strat_home_nav()
            world_bank_viz_nav()
            map_demo_nav()

        if role == "usaid_worker":
            usaid_worker_home_nav()
            ngo_directory_nav()
            add_ngo_nav()
            prediction_nav()
            api_test_nav()
            classification_nav()

        if role == "administrator":
            admin_home_nav()
            ml_model_mgmt_nav()

    about_page_nav()

    if st.session_state["authenticated"]:
        if st.sidebar.button("Logout"):
            st.session_state.pop("role", None)
            st.session_state.pop("user_id", None)
            st.session_state.pop("first_name", None)
            st.session_state["authenticated"] = False

            st.switch_page("Home.py")