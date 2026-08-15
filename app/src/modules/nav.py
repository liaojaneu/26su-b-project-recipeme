# Idea borrowed from:
# https://github.com/fsmosca/sample-streamlit-authenticator

# This file adds sidebar navigation links based on
# the currently logged-in RecipeMe persona.

import streamlit as st


# ---------------------------------------------------------------------------
# General navigation
# ---------------------------------------------------------------------------

def home_nav():
    st.sidebar.page_link(
        "Home.py",
        label="Home",
        icon="🏠",
    )


def about_page_nav():
    st.sidebar.page_link(
        "pages/30_About.py",
        label="About RecipeMe",
        icon="ℹ️",
    )


# ---------------------------------------------------------------------------
# Rachel Green: Home Cook
# ---------------------------------------------------------------------------

def rachel_home_nav():
    st.sidebar.page_link(
        "pages/00_Rachel_Home.py",
        label="Rachel Home",
        icon="🏠",
    )


def discover_recipes_nav():
    st.sidebar.page_link(
        "pages/01_Discover_Recipes.py",
        label="Discover Recipes",
        icon="🔎",
    )


def my_collections_nav():
    st.sidebar.page_link(
        "pages/02_My_Collections.py",
        label="My Collections",
        icon="📚",
    )


def reviews_and_creators_nav():
    st.sidebar.page_link(
        "pages/03_Reviews_and_Creators.py",
        label="Reviews and Creators",
        icon="⭐",
    )


# ---------------------------------------------------------------------------
# Mark Smith: Professional Chef
# ---------------------------------------------------------------------------

def mark_home_nav():
    st.sidebar.page_link(
        "pages/10_Mark_Home.py",
        label="Mark Home",
        icon="🏠",
    )


def manage_recipes_nav():
    st.sidebar.page_link(
        "pages/11_Manage_Recipes.py",
        label="Manage Recipes",
        icon="📝",
    )


def ingredients_and_tags_nav():
    st.sidebar.page_link(
        "pages/12_Ingredients_and_Tags.py",
        label="Ingredients and Tags",
        icon="🥕",
    )


def recipe_engagement_nav():
    st.sidebar.page_link(
        "pages/13_Recipe_Engagement.py",
        label="Recipe Engagement",
        icon="📊",
    )


# ---------------------------------------------------------------------------
# Clark Johnson: Recipe Content Creator
# ---------------------------------------------------------------------------

def clark_home_nav():
    st.sidebar.page_link(
        "pages/20_Clark_Home.py",
        label="Clark Home",
        icon="🏠",
    )


def creator_content_nav():
    st.sidebar.page_link(
        "pages/21_Creator_Content.py",
        label="Creator Content",
        icon="🎥",
    )


def audience_reviews_nav():
    st.sidebar.page_link(
        "pages/22_Audience_Reviews.py",
        label="Audience Reviews",
        icon="💬",
    )


def themed_collections_nav():
    st.sidebar.page_link(
        "pages/23_Themed_Collections.py",
        label="Themed Collections",
        icon="📂",
    )


# ---------------------------------------------------------------------------
# David Lopez: System Administrator
# ---------------------------------------------------------------------------

def admin_home_nav():
    st.sidebar.page_link(
        "pages/20_Admin_Home.py",
        label="Admin Home",
        icon="🖥️",
    )


# ---------------------------------------------------------------------------
# Sidebar assembly
# ---------------------------------------------------------------------------

def SideBarLinks(show_home=False):
    """
    Display sidebar links based on the logged-in RecipeMe user's role.

    Expected roles:
        home_cook
        chef
        creator
        administrator
    """

    st.sidebar.image(
        "assets/recipeme_logo.png",
        width=200,
    )

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Redirect unauthenticated users to the login page.
    if not st.session_state["authenticated"] and not show_home:
        st.switch_page("Home.py")

    if show_home:
        home_nav()

    if st.session_state["authenticated"]:
        role = st.session_state.get("role")

        if role == "home_cook":
            rachel_home_nav()
            discover_recipes_nav()
            my_collections_nav()
            reviews_and_creators_nav()

        elif role == "chef":
            mark_home_nav()
            manage_recipes_nav()
            ingredients_and_tags_nav()
            recipe_engagement_nav()

        elif role == "creator":
            clark_home_nav()
            creator_content_nav()
            audience_reviews_nav()
            themed_collections_nav()

        elif role == "administrator":
            admin_home_nav()

        else:
            st.sidebar.warning(
                "Your account does not have a recognized role."
            )

    about_page_nav()

    if st.session_state["authenticated"]:
        if st.sidebar.button(
            "Logout",
            use_container_width=True,
        ):
            st.session_state.pop("role", None)
            st.session_state.pop("user_id", None)
            st.session_state.pop("first_name", None)
            st.session_state["authenticated"] = False

            st.switch_page("Home.py")