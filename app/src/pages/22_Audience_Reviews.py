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

st.header("Audience Reviews and Replies")
st.write("Read audience feedback and respond directly to reviews.")

recipe_id = st.number_input("Recipe ID", min_value=1, step=1)
if st.button("Load Recipe Reviews", type="primary", use_container_width=True):
    try:
        response = requests.get(
            f"{API_URL}/review/reviews", params={"recipe_id": int(recipe_id)}, timeout=10
        )
        response.raise_for_status()
        st.dataframe(response.json(), use_container_width=True, hide_index=True)
    except requests.RequestException as error:
        logger.error("Could not retrieve reviews: %s", error)
        st.error("Could not retrieve reviews.")

st.divider()
st.subheader("Review Details and Existing Replies")
review_id = st.number_input("Review ID", min_value=1, step=1)
if st.button("View Review Details", use_container_width=True):
    response = requests.get(f"{API_URL}/review/reviews/{int(review_id)}", timeout=10)
    if response.ok:
        st.json(response.json())
    else:
        st.error(response.json().get("error", "Review not found."))

with st.form("reply_to_review"):
    reply_text = st.text_area("Your reply")
    submitted = st.form_submit_button("Post Reply", type="primary")
if submitted:
    response = requests.post(
        f"{API_URL}/review/actions",
        json={"resource": "reply", "review_id": int(review_id),
              "user_id": USER_ID, "reply_text": reply_text}, timeout=10,
    )
    st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))

st.divider()
st.subheader("Edit a Reply")
reply_id = st.number_input("Reply ID", min_value=1, step=1)
updated_reply = st.text_area("Updated reply")
if st.button("Update Reply", type="primary", use_container_width=True):
    response = requests.put(
        f"{API_URL}/review/content/reply/{int(reply_id)}",
        json={"reply_text": updated_reply}, timeout=10,
    )
    st.success(response.json()["message"]) if response.ok else st.error(response.json().get("error"))

