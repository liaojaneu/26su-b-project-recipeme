import logging
import os

import requests
import streamlit as st

from modules.nav import SideBarLinks


logger = logging.getLogger(__name__)
API_URL = os.getenv("API_URL", "http://api:4000")
USER_ID = st.session_state.get("user_id", 2)

st.set_page_config(layout="wide")
SideBarLinks()

st.header("Publish and Manage Recipes")
st.write(f"### Hi, Chef {st.session_state.get('first_name', 'Mark')}.")

try:
    response = requests.get(f"{API_URL}/user/users/{USER_ID}/recipes", timeout=10)
    response.raise_for_status()
    st.dataframe(response.json(), use_container_width=True, hide_index=True)
except requests.RequestException as error:
    logger.error("Could not retrieve recipes: %s", error)
    st.error("Could not retrieve your recipes.")

publish_tab, edit_tab, archive_tab = st.tabs(["Publish", "Edit", "Archive or Restore"])

with publish_tab:
    with st.form("publish_recipe"):
        title = st.text_input("Recipe title")
        description = st.text_area("Description")
        column_1, column_2, column_3 = st.columns(3)
        prep_minutes = column_1.number_input("Prep minutes", min_value=0, step=5)
        cook_minutes = column_2.number_input("Cook minutes", min_value=0, step=5)
        difficulty = column_3.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
        cooking_tips = st.text_area("Cooking tips")
        substitutions = st.text_area("Substitutions")
        serving_suggestions = st.text_area("Serving suggestions")
        publish_submitted = st.form_submit_button("Publish Recipe", type="primary")
    if publish_submitted:
        response = requests.post(
            f"{API_URL}/recipe/recipes",
            json={"creator_id": USER_ID, "title": title, "description": description,
                  "prep_minutes": int(prep_minutes), "cook_minutes": int(cook_minutes),
                  "difficulty": difficulty, "cooking_tips": cooking_tips,
                  "substitutions": substitutions,
                  "serving_suggestions": serving_suggestions}, timeout=10,
        )
        if response.ok:
            st.success(f"Recipe {response.json()['recipe_id']} was published.")
        else:
            st.error(response.json().get("error", "Could not publish recipe."))

with edit_tab:
    recipe_id = st.number_input("Recipe ID", min_value=1, step=1, key="edit_recipe")
    updated_description = st.text_area("Updated description")
    updated_tips = st.text_area("Updated cooking tips")
    if st.button("Update Recipe", type="primary", use_container_width=True):
        response = requests.put(
            f"{API_URL}/recipe/recipes/{int(recipe_id)}",
            json={"description": updated_description, "cooking_tips": updated_tips}, timeout=10,
        )
        st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))

with archive_tab:
    archive_id = st.number_input("Recipe ID", min_value=1, step=1, key="archive_recipe")
    active_status = st.selectbox("Recipe status", ["Active", "Archived"])
    if st.button("Change Recipe Status", type="primary", use_container_width=True):
        response = requests.put(
            f"{API_URL}/recipe/recipes/{int(archive_id)}",
            json={"is_active": active_status == "Active"}, timeout=10,
        )
        st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))

