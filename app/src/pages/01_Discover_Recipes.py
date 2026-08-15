import logging
import os

import requests
import streamlit as st

from modules.nav import SideBarLinks


logger = logging.getLogger(__name__)
API_URL = os.getenv("API_URL", "http://api:4000")

st.set_page_config(layout="wide")
SideBarLinks()

st.header("Discover Recipes")
st.write(f"### Hi, {st.session_state.get('first_name', 'Rachel')}.")
st.write("Search RecipeMe by ingredient, tag, difficulty, or total cooking time.")

column_1, column_2, column_3, column_4 = st.columns(4)
with column_1:
    ingredient = st.text_input("Ingredient")
with column_2:
    tag = st.text_input("Tag")
with column_3:
    difficulty = st.selectbox("Difficulty", ["Any", "Easy", "Medium", "Hard"])
with column_4:
    max_minutes = st.number_input("Maximum total minutes", min_value=0, step=5)

if st.button("Search Recipes", type="primary", use_container_width=True):
    params = {}
    if ingredient:
        params["ingredient"] = ingredient
    if tag:
        params["tag"] = tag
    if difficulty != "Any":
        params["difficulty"] = difficulty
    if max_minutes > 0:
        params["max_minutes"] = int(max_minutes)

    try:
        response = requests.get(f"{API_URL}/recipe/recipes", params=params, timeout=10)
        response.raise_for_status()
        recipes = response.json()
        if recipes:
            st.dataframe(recipes, use_container_width=True, hide_index=True)
        else:
            st.info("No recipes matched those filters.")
    except requests.RequestException as error:
        logger.error("Could not retrieve recipes: %s", error)
        st.error("Could not retrieve recipes. Make sure the API is running.")

st.divider()
st.subheader("Recipe Details")
recipe_id = st.number_input("Recipe ID", min_value=1, step=1)

if st.button("View Recipe", use_container_width=True):
    try:
        response = requests.get(f"{API_URL}/recipe/recipes/{int(recipe_id)}", timeout=10)
        if not response.ok:
            st.error(response.json().get("error", "Recipe not found."))
        else:
            recipe = response.json()
            st.subheader(recipe["title"])
            st.write(recipe.get("description", ""))
            st.write(
                f"**Creator:** {recipe.get('creator_name', 'Unknown')} | "
                f"**Difficulty:** {recipe.get('difficulty', 'Not listed')} | "
                f"**Time:** {recipe.get('prep_minutes', 0) + recipe.get('cook_minutes', 0)} minutes"
            )
            st.write("#### Ingredients")
            st.dataframe(recipe.get("ingredients", []), use_container_width=True, hide_index=True)
            st.write("#### Steps")
            st.dataframe(recipe.get("steps", []), use_container_width=True, hide_index=True)
            st.write("#### Tags")
            st.dataframe(recipe.get("tags", []), use_container_width=True, hide_index=True)
    except requests.RequestException as error:
        logger.error("Could not retrieve recipe: %s", error)
        st.error("Could not retrieve the recipe.")

