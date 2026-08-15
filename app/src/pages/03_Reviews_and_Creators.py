import logging
import os

import requests
import streamlit as st

from modules.nav import SideBarLinks


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Reviews and Creators",
    page_icon="⭐",
    layout="wide",
)

SideBarLinks()


# ---------------------------------------------------------------------------
# API and user configuration
# ---------------------------------------------------------------------------

# This is the internal Docker hostname used by the Streamlit container.
API_URL = os.getenv(
    "API_URL",
    "http://web-api:4000",
).rstrip("/")

USER_ID = st.session_state.get("user_id", 1)
FIRST_NAME = st.session_state.get("first_name", "Rachel")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def parse_api_response(response):
    """
    Convert an API response to JSON.

    If Flask returns an HTML error page or an empty response,
    display the actual status and response instead of crashing.
    """

    try:
        return response.json()

    except requests.exceptions.JSONDecodeError:
        st.error(
            f"The API returned HTTP {response.status_code}, "
            "but the response was not valid JSON."
        )

        if response.text:
            st.code(response.text[:2000])
        else:
            st.code("The API response body was empty.")

        logger.error(
            "Non-JSON API response: status=%s body=%s",
            response.status_code,
            response.text,
        )

        return None


def show_api_error(response_data, default_message):
    """
    Display an error message returned by the RecipeMe API.
    """

    if isinstance(response_data, dict):
        st.error(
            response_data.get(
                "error",
                default_message,
            )
        )
    else:
        st.error(default_message)


def show_connection_error(error):
    """
    Display a readable message when Streamlit cannot reach Flask.
    """

    logger.error(
        "Could not connect to RecipeMe API: %s",
        error,
    )

    st.error(
        f"Could not connect to the RecipeMe API at {API_URL}. "
        "Check that the API container is running."
    )


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

st.header("Reviews and Creators")
st.write(f"### Hi, {FIRST_NAME}.")

review_tab, following_tab = st.tabs(
    [
        "Recipe Reviews",
        "Followed Creators",
    ]
)


# ---------------------------------------------------------------------------
# Recipe Reviews tab
# ---------------------------------------------------------------------------

with review_tab:
    st.subheader("View Recipe Reviews")

    recipe_id = st.number_input(
        "Recipe ID",
        min_value=1,
        step=1,
        key="review_recipe_id",
    )

    if st.button(
        "View Reviews",
        type="primary",
        use_container_width=True,
    ):
        try:
            response = requests.get(
                f"{API_URL}/review/reviews",
                params={
                    "recipe_id": int(recipe_id),
                    "status": "active",
                },
                timeout=10,
            )

            response_data = parse_api_response(response)

            if response_data is not None:
                if response.ok:
                    if response_data:
                        st.dataframe(
                            response_data,
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info(
                            "This recipe does not have any reviews yet."
                        )
                else:
                    show_api_error(
                        response_data,
                        "Could not retrieve reviews.",
                    )

        except requests.exceptions.RequestException as error:
            show_connection_error(error)

    st.divider()
    st.subheader("Leave a Review")

    with st.form("leave_review_form"):
        rating = st.slider(
            "Rating",
            min_value=1,
            max_value=5,
            value=5,
        )

        review_text = st.text_area(
            "Your review",
            placeholder="What did you think of this recipe?",
        )

        review_submitted = st.form_submit_button(
            "Submit Review",
            type="primary",
            use_container_width=True,
        )

    if review_submitted:
        if not review_text.strip():
            st.warning(
                "Please enter review text before submitting."
            )

        else:
            try:
                response = requests.post(
                    f"{API_URL}/review/actions",
                    json={
                        "resource": "review",
                        "recipe_id": int(recipe_id),
                        "user_id": int(USER_ID),
                        "rating": int(rating),
                        "review_text": review_text.strip(),
                    },
                    timeout=10,
                )

                response_data = parse_api_response(response)

                if response_data is not None:
                    if response.ok:
                        st.success(
                            response_data.get(
                                "message",
                                "Review submitted successfully.",
                            )
                        )

                        if "id" in response_data:
                            st.caption(
                                "New review ID: "
                                f"{response_data['id']}"
                            )
                    else:
                        show_api_error(
                            response_data,
                            "Could not submit the review.",
                        )

            except requests.exceptions.RequestException as error:
                show_connection_error(error)


# ---------------------------------------------------------------------------
# Followed Creators tab
# ---------------------------------------------------------------------------

with following_tab:
    st.subheader("Creators You Follow")

    try:
        response = requests.get(
            f"{API_URL}/user/users/{int(USER_ID)}/following",
            timeout=10,
        )

        response_data = parse_api_response(response)

        if response_data is not None:
            if response.ok:
                if response_data:
                    st.dataframe(
                        response_data,
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info(
                        "You are not following any creators yet."
                    )
            else:
                show_api_error(
                    response_data,
                    "Could not retrieve followed creators.",
                )

    except requests.exceptions.RequestException as error:
        show_connection_error(error)

    st.divider()
    st.subheader("Manage Followed Creators")

    creator_id = st.number_input(
        "Creator User ID",
        min_value=1,
        step=1,
        key="creator_user_id",
    )

    follow_column, unfollow_column = st.columns(2)

    if follow_column.button(
        "Follow Creator",
        type="primary",
        use_container_width=True,
    ):
        if int(creator_id) == int(USER_ID):
            st.warning(
                "You cannot follow your own account."
            )

        else:
            try:
                response = requests.post(
                    f"{API_URL}/user/follows",
                    json={
                        "follower_id": int(USER_ID),
                        "creator_id": int(creator_id),
                    },
                    timeout=10,
                )

                response_data = parse_api_response(response)

                if response_data is not None:
                    if response.ok:
                        st.success(
                            response_data.get(
                                "message",
                                "Creator followed successfully.",
                            )
                        )
                    else:
                        show_api_error(
                            response_data,
                            "Could not follow the creator.",
                        )

            except requests.exceptions.RequestException as error:
                show_connection_error(error)

    if unfollow_column.button(
        "Unfollow Creator",
        use_container_width=True,
    ):
        try:
            response = requests.delete(
                (
                    f"{API_URL}/user/follows/"
                    f"{int(USER_ID)}/{int(creator_id)}"
                ),
                timeout=10,
            )

            response_data = parse_api_response(response)

            if response_data is not None:
                if response.ok:
                    st.success(
                        response_data.get(
                            "message",
                            "Creator unfollowed successfully.",
                        )
                    )
                else:
                    show_api_error(
                        response_data,
                        "Could not unfollow the creator.",
                    )

        except requests.exceptions.RequestException as error:
            show_connection_error(error)