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

st.header("Themed Recipe Collections")
st.write("Organize your catalog into collections your followers can browse.")

try:
    response = requests.get(
        f"{API_URL}/collection/collections", params={"user_id": USER_ID}, timeout=10
    )
    response.raise_for_status()
    st.dataframe(response.json(), use_container_width=True, hide_index=True)
except requests.RequestException as error:
    logger.error("Could not retrieve collections: %s", error)
    st.error("Could not retrieve your collections.")

create_tab, add_tab, inspect_tab, delete_tab = st.tabs(
    ["Create", "Add Recipe", "Inspect", "Delete"]
)

with create_tab:
    with st.form("creator_collection"):
        collection_name = st.text_input("Collection name")
        description = st.text_area("Description")
        submitted = st.form_submit_button("Create Collection", type="primary")
    if submitted:
        response = requests.post(
            f"{API_URL}/collection/actions",
            json={"resource": "collection", "user_id": USER_ID,
                  "collection_name": collection_name, "description": description}, timeout=10,
        )
        st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))

with add_tab:
    collection_id = st.number_input("Collection ID", min_value=1, step=1, key="add_collection")
    recipe_id = st.number_input("Recipe ID", min_value=1, step=1, key="add_recipe")
    if st.button("Add Recipe", type="primary", use_container_width=True):
        response = requests.post(
            f"{API_URL}/collection/actions",
            json={"resource": "collection_recipe", "collection_id": int(collection_id),
                  "recipe_id": int(recipe_id)}, timeout=10,
        )
        st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))

with inspect_tab:
    inspect_id = st.number_input("Collection ID", min_value=1, step=1, key="inspect_collection")
    if st.button("View Collection", type="primary", use_container_width=True):
        response = requests.get(
            f"{API_URL}/collection/collections/{int(inspect_id)}", timeout=10
        )
        st.json(response.json()) if response.ok else st.error(response.json().get("error"))

with delete_tab:
    delete_id = st.number_input("Collection ID", min_value=1, step=1, key="delete_collection")
    confirm = st.checkbox("I understand this deletes the collection.")
    if st.button("Delete Collection", type="primary", use_container_width=True, disabled=not confirm):
        response = requests.delete(
            f"{API_URL}/collection/actions",
            params={"resource": "collection", "collection_id": int(delete_id)}, timeout=10,
        )
        st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))
