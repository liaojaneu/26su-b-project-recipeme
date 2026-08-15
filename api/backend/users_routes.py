"""General RecipeMe API routes for users and follow relationships."""

from flask import Blueprint, current_app, jsonify, request
from mysql.connector import Error

from backend.db_connection import get_db


users = Blueprint("users", __name__)


# Get users with optional role and account-status filters.
# Example: GET /user/users?role=creator&account_status=active
@users.route("/users", methods=["GET"])
def get_all_users():
    cursor = get_db().cursor(dictionary=True)
    try:
        role = request.args.get("role")
        account_status = request.args.get("account_status")
        query = """
            SELECT user_id, full_name, email, role, account_status, created_at
            FROM users WHERE 1 = 1
        """
        params = []
        if role:
            query += " AND role = %s"
            params.append(role)
        if account_status:
            query += " AND account_status = %s"
            params.append(account_status)
        query += " ORDER BY full_name"
        cursor.execute(query, params)
        user_list = cursor.fetchall()
        current_app.logger.info(f"Retrieved {len(user_list)} users")
        return jsonify(user_list), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get one user with recipe, review, follower, and following counts.
# Example: GET /user/users/3
@users.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT user_id, full_name, email, role, account_status, created_at
            FROM users WHERE user_id = %s
            """,
            (user_id,),
        )
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        count_queries = {
            "recipe_count": "SELECT COUNT(*) AS count FROM recipes WHERE creator_id = %s",
            "review_count": "SELECT COUNT(*) AS count FROM reviews WHERE user_id = %s",
            "follower_count": "SELECT COUNT(*) AS count FROM follows WHERE creator_id = %s",
            "following_count": "SELECT COUNT(*) AS count FROM follows WHERE follower_id = %s",
        }
        for key, query in count_queries.items():
            cursor.execute(query, (user_id,))
            user[key] = cursor.fetchone()["count"]
        return jsonify(user), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get recipes created by one user.
# Example: GET /user/users/3/recipes
@users.route("/users/<int:user_id>/recipes", methods=["GET"])
def get_user_recipes(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT recipe_id, title, description, prep_minutes, cook_minutes,
                   difficulty, media_url, is_active
            FROM recipes WHERE creator_id = %s ORDER BY recipe_id DESC
            """,
            (user_id,),
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get users followed by one user.
# Example: GET /user/users/1/following
@users.route("/users/<int:user_id>/following", methods=["GET"])
def get_following(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT users.user_id, users.full_name, users.role, follows.followed_at
            FROM follows JOIN users ON follows.creator_id = users.user_id
            WHERE follows.follower_id = %s ORDER BY users.full_name
            """,
            (user_id,),
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get followers of one creator.
# Example: GET /user/users/3/followers
@users.route("/users/<int:user_id>/followers", methods=["GET"])
def get_followers(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT users.user_id, users.full_name, users.role, follows.followed_at
            FROM follows JOIN users ON follows.follower_id = users.user_id
            WHERE follows.creator_id = %s ORDER BY users.full_name
            """,
            (user_id,),
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a follow relationship.
# Example: POST /user/follows with {"follower_id": 1, "creator_id": 3}
@users.route("/follows", methods=["POST"])
def create_follow():
    database = get_db()
    cursor = database.cursor(dictionary=True)
    try:
        data = request.get_json(silent=True) or {}
        if data.get("follower_id") is None or data.get("creator_id") is None:
            return jsonify({"error": "follower_id and creator_id are required"}), 400
        cursor.execute(
            "INSERT INTO follows (follower_id, creator_id) VALUES (%s, %s)",
            (data["follower_id"], data["creator_id"]),
        )
        database.commit()
        return jsonify({"message": "Creator followed successfully"}), 201
    except Error as e:
        database.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update user profile or account status.
# Example: PUT /user/users/4 with {"account_status": "suspended"}
@users.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    database = get_db()
    cursor = database.cursor(dictionary=True)
    try:
        data = request.get_json(silent=True) or {}
        allowed_fields = ["full_name", "email", "role", "account_status"]
        update_fields = [f"{field} = %s" for field in allowed_fields if field in data]
        params = [data[field] for field in allowed_fields if field in data]
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400
        params.append(user_id)
        cursor.execute(
            f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s",
            params,
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "User not found"}), 404
        database.commit()
        return jsonify({"message": "User updated successfully"}), 200
    except Error as e:
        database.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a follow relationship (unfollow).
# Example: DELETE /user/follows/1/3
@users.route("/follows/<int:follower_id>/<int:creator_id>", methods=["DELETE"])
def delete_follow(follower_id, creator_id):
    database = get_db()
    cursor = database.cursor(dictionary=True)
    try:
        cursor.execute(
            "DELETE FROM follows WHERE follower_id = %s AND creator_id = %s",
            (follower_id, creator_id),
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Follow relationship not found"}), 404
        database.commit()
        return jsonify({"message": "Creator unfollowed successfully"}), 200
    except Error as e:
        database.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
