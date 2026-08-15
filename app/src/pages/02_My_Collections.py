import logging
import os

import requests
import streamlit as st

from modules.nav import SideBarLinks


logger = logging.getLogger(__name__)
API_URL = os.getenv("API_URL", "http://api:4000")
USER_ID = st.session_state.get("user_id", 1)

st.set_page_config(layout="wide")
SideBarLinks()

st.header("My Recipe Collections")
st.write(f"### Hi, {st.session_state.get('first_name', 'Rachel')}.")

try:
    response = requests.get(
        f"{API_URL}/collection/collections", params={"user_id": USER_ID}, timeout=10
    )
    response.raise_for_status()
    collection_list = response.json()
    st.dataframe(collection_list, use_container_width=True, hide_index=True)
except requests.RequestException as error:
    logger.error("Could not retrieve collections: %s", error)
    st.error("Could not retrieve your collections.")

create_tab, save_tab, edit_tab, remove_tab = st.tabs(
    ["Create Collection", "Save Recipe", "Edit Collection", "Remove"]
)

with create_tab:
    with st.form("create_collection"):
        name = st.text_input("Collection name")
        description = st.text_area("Description")
        create_submitted = st.form_submit_button("Create Collection", type="primary")
    if create_submitted:
        response = requests.post(
            f"{API_URL}/collection/actions",
            json={"resource": "collection", "user_id": USER_ID,
                  "collection_name": name, "description": description},
            timeout=10,
        )
        if response.ok:
            st.success(response.json()["message"])
        else:
            st.error(response.json().get("error", "Could not create collection."))

with save_tab:
    collection_id = st.number_input("Collection ID", min_value=1, step=1, key="save_collection")
    recipe_id = st.number_input("Recipe ID", min_value=1, step=1, key="save_recipe")
    if st.button("Save Recipe", type="primary", use_container_width=True):
        response = requests.post(
            f"{API_URL}/collection/actions",
            json={"resource": "collection_recipe", "collection_id": int(collection_id),
                  "recipe_id": int(recipe_id)},
            timeout=10,
        )
        st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))

with edit_tab:
    edit_id = st.number_input("Collection ID", min_value=1, step=1, key="edit_collection")
    new_name = st.text_input("New collection name")
    new_description = st.text_area("New description")
    if st.button("Update Collection", type="primary", use_container_width=True):
        payload = {}
        if new_name:
            payload["collection_name"] = new_name
        if new_description:
            payload["description"] = new_description
        response = requests.put(
            f"{API_URL}/collection/collections/{int(edit_id)}", json=payload, timeout=10
        )
        st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))

with remove_tab:
    remove_collection_id = st.number_input("Collection ID", min_value=1, step=1, key="remove_collection")
    remove_recipe_id = st.number_input("Recipe ID", min_value=1, step=1, key="remove_recipe")
    if st.button("Remove Recipe from Collection", type="primary", use_container_width=True):
        response = requests.delete(
            f"{API_URL}/collection/actions",
            params={"resource": "collection_recipe", "collection_id": int(remove_collection_id),
                    "recipe_id": int(remove_recipe_id)},
            timeout=10,
        )
        st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))

