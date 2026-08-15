import logging
import os

import requests
import streamlit as st

from modules.nav import SideBarLinks


logger = logging.getLogger(__name__)
API_URL = os.getenv("API_URL", "http://api:4000")

st.set_page_config(layout="wide")
SideBarLinks()

st.header("Ingredients and Searchable Tags")
st.write("Browse RecipeMe lookup data and assign searchable tags to recipes.")

ingredient_tab, tag_tab, recipe_tab = st.tabs(["Ingredients", "Tags", "Recipe Components"])

with ingredient_tab:
    ingredient_name = st.text_input("Search ingredient name")
    if st.button("Load Ingredients", type="primary", use_container_width=True):
        params = {"name": ingredient_name} if ingredient_name else {}
        response = requests.get(f"{API_URL}/collection/ingredients", params=params, timeout=10)
        if response.ok:
            st.dataframe(response.json(), use_container_width=True, hide_index=True)
        else:
            st.error(response.json().get("error", "Could not retrieve ingredients."))

with tag_tab:
    tag_type = st.selectbox(
        "Tag type", ["All", "Cuisine", "Dietary", "Category", "Difficulty", "Time", "Occasion"]
    )
    if st.button("Load Tags", type="primary", use_container_width=True):
        params = {"tag_type": tag_type} if tag_type != "All" else {}
        response = requests.get(f"{API_URL}/collection/tags", params=params, timeout=10)
        if response.ok:
            st.dataframe(response.json(), use_container_width=True, hide_index=True)

    recipe_id = st.number_input("Recipe ID", min_value=1, step=1, key="tag_recipe")
    tag_id = st.number_input("Tag ID", min_value=1, step=1)
    column_1, column_2 = st.columns(2)
    if column_1.button("Assign Tag", type="primary", use_container_width=True):
        response = requests.post(
            f"{API_URL}/collection/actions",
            json={"resource": "recipe_tag", "recipe_id": int(recipe_id),
                  "tag_id": int(tag_id)}, timeout=10,
        )
        st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))
    if column_2.button("Remove Tag", use_container_width=True):
        response = requests.delete(
            f"{API_URL}/collection/actions",
            params={"resource": "recipe_tag", "recipe_id": int(recipe_id),
                    "tag_id": int(tag_id)}, timeout=10,
        )
        st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))

with recipe_tab:
    component_recipe_id = st.number_input("Recipe ID", min_value=1, step=1, key="component_recipe")
    if st.button("View Ingredients and Steps", type="primary", use_container_width=True):
        ingredients = requests.get(
            f"{API_URL}/recipe/recipes/{int(component_recipe_id)}/ingredients", timeout=10
        )
        steps = requests.get(
            f"{API_URL}/recipe/recipes/{int(component_recipe_id)}/steps", timeout=10
        )
        st.write("#### Ingredients")
        st.dataframe(ingredients.json(), use_container_width=True, hide_index=True)
        st.write("#### Steps")
        st.dataframe(steps.json(), use_container_width=True, hide_index=True)

