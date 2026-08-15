import logging
import os

import requests
import streamlit as st

from modules.nav import SideBarLinks


logger = logging.getLogger(__name__)
API_URL = os.getenv("API_URL", "http://api:4000")
USER_ID = st.session_state.get("user_id", 3)

st.set_page_config(layout="wide")
SideBarLinks()

st.header("Manage Creator Content")
st.write(f"### Hi, {st.session_state.get('first_name', 'Clark')}.")

try:
    response = requests.get(f"{API_URL}/user/users/{USER_ID}/recipes", timeout=10)
    response.raise_for_status()
    st.dataframe(response.json(), use_container_width=True, hide_index=True)
except requests.RequestException as error:
    logger.error("Could not retrieve creator recipes: %s", error)
    st.error("Could not retrieve your recipes.")

publish_tab, refine_tab, links_tab = st.tabs(["Publish Recipe", "Refine Recipe", "External Links"])

with publish_tab:
    with st.form("creator_publish"):
        title = st.text_input("Recipe title")
        description = st.text_area("Description")
        column_1, column_2, column_3 = st.columns(3)
        prep = column_1.number_input("Prep minutes", min_value=0, step=5)
        cook = column_2.number_input("Cook minutes", min_value=0, step=5)
        difficulty = column_3.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
        media_url = st.text_input("Image or video URL")
        submitted = st.form_submit_button("Publish Recipe", type="primary")
    if submitted:
        response = requests.post(
            f"{API_URL}/recipe/recipes",
            json={"creator_id": USER_ID, "title": title, "description": description,
                  "prep_minutes": int(prep), "cook_minutes": int(cook),
                  "difficulty": difficulty, "media_url": media_url}, timeout=10,
        )
        st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))

with refine_tab:
    recipe_id = st.number_input("Recipe ID", min_value=1, step=1, key="refine_recipe")
    description = st.text_area("Revised description")
    cooking_tips = st.text_area("Revised cooking tips")
    if st.button("Update Published Recipe", type="primary", use_container_width=True):
        response = requests.put(
            f"{API_URL}/recipe/recipes/{int(recipe_id)}",
            json={"description": description, "cooking_tips": cooking_tips}, timeout=10,
        )
        st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))

with links_tab:
    link_recipe_id = st.number_input("Recipe ID", min_value=1, step=1, key="link_recipe")
    if st.button("View Recipe and Links", use_container_width=True):
        response = requests.get(
            f"{API_URL}/recipe/recipes/{int(link_recipe_id)}", timeout=10
        )
        if response.ok:
            recipe = response.json()
            st.dataframe(recipe.get("external_links", []), use_container_width=True, hide_index=True)
        else:
            st.error(response.json().get("error", "Recipe not found."))

