import logging
import os

import pandas as pd
import requests
import streamlit as st

from modules.nav import SideBarLinks


logger = logging.getLogger(__name__)
API_URL = os.getenv("API_URL", "http://api:4000")
USER_ID = st.session_state.get("user_id", 2)

st.set_page_config(layout="wide")
SideBarLinks()

st.header("Recipe Engagement")
st.write("Compare saves, reviews, and average ratings for your recipes.")

try:
    response = requests.get(f"{API_URL}/user/users/{USER_ID}/recipes", timeout=10)
    response.raise_for_status()
    chef_recipes = response.json()

    engagement_rows = []
    for recipe in chef_recipes:
        engagement_response = requests.get(
            f"{API_URL}/recipe/recipes/{recipe['recipe_id']}/engagement", timeout=10
        )
        if engagement_response.ok:
            engagement_rows.append(engagement_response.json())

    if engagement_rows:
        engagement_data = pd.DataFrame(engagement_rows)
        st.dataframe(engagement_data, use_container_width=True, hide_index=True)
        st.write("### Saves by Recipe")
        st.bar_chart(engagement_data.set_index("title")["saves"])
        st.write("### Average Rating by Recipe")
        st.bar_chart(engagement_data.set_index("title")["average_rating"])
    else:
        st.info("No engagement data is available yet.")
except requests.RequestException as error:
    logger.error("Could not retrieve engagement: %s", error)
    st.error("Could not retrieve engagement data.")
