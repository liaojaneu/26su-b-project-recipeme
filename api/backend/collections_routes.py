"""General RecipeMe API routes for collections, tags, and lookup data."""

from flask import Blueprint, current_app, jsonify, request
from mysql.connector import Error

from backend.db_connection import get_db


collections = Blueprint("collections", __name__)


# Get collections with an optional owner filter.
# Example: GET /collection/collections?user_id=1
@collections.route("/collections", methods=["GET"])
def get_all_collections():
    cursor = get_db().cursor(dictionary=True)
    try:
        user_id = request.args.get("user_id", type=int)
        query = """
            SELECT collections.collection_id, collections.user_id,
                   users.full_name AS owner_name,
                   collections.collection_name, collections.description,
                   COUNT(collection_recipes.recipe_id) AS recipe_count
            FROM collections
            JOIN users ON collections.user_id = users.user_id
            LEFT JOIN collection_recipes
                ON collections.collection_id = collection_recipes.collection_id
        """
        params = []
        if user_id is not None:
            query += " WHERE collections.user_id = %s"
            params.append(user_id)
        query += """
            GROUP BY collections.collection_id, collections.user_id,
                     users.full_name, collections.collection_name,
                     collections.description
            ORDER BY collections.collection_name
        """
        cursor.execute(query, params)
        collection_list = cursor.fetchall()
        current_app.logger.info(f"Retrieved {len(collection_list)} collections")
        return jsonify(collection_list), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get one collection and its recipes.
# Example: GET /collection/collections/1
@collections.route("/collections/<int:collection_id>", methods=["GET"])
def get_collection(collection_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT collections.*, users.full_name AS owner_name
            FROM collections JOIN users ON collections.user_id = users.user_id
            WHERE collections.collection_id = %s
            """,
            (collection_id,),
        )
        collection = cursor.fetchone()
        if not collection:
            return jsonify({"error": "Collection not found"}), 404
        cursor.execute(
            """
            SELECT recipes.recipe_id, recipes.title, recipes.description,
                   recipes.prep_minutes, recipes.cook_minutes,
                   collection_recipes.added_at
            FROM collection_recipes
            JOIN recipes ON collection_recipes.recipe_id = recipes.recipe_id
            WHERE collection_recipes.collection_id = %s
            ORDER BY collection_recipes.added_at DESC
            """,
            (collection_id,),
        )
        collection["recipes"] = cursor.fetchall()
        return jsonify(collection), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get recipes saved in one collection.
# Example: GET /collection/collections/1/recipes
@collections.route("/collections/<int:collection_id>/recipes", methods=["GET"])
def get_collection_recipes(collection_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT recipes.recipe_id, recipes.title, recipes.description,
                   collection_recipes.added_at
            FROM collection_recipes
            JOIN recipes ON collection_recipes.recipe_id = recipes.recipe_id
            WHERE collection_recipes.collection_id = %s
            ORDER BY collection_recipes.added_at DESC
            """,
            (collection_id,),
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get ingredient lookup data with optional name search.
# Example: GET /collection/ingredients?name=garlic
@collections.route("/ingredients", methods=["GET"])
def get_ingredients():
    cursor = get_db().cursor(dictionary=True)
    try:
        name = request.args.get("name")
        query = "SELECT ingredient_id, ingredient_name FROM ingredients"
        params = []
        if name:
            query += " WHERE ingredient_name LIKE %s"
            params.append(f"%{name}%")
        query += " ORDER BY ingredient_name"
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get tag lookup data with optional tag-type filter.
# Example: GET /collection/tags?tag_type=Dietary
@collections.route("/tags", methods=["GET"])
def get_tags():
    cursor = get_db().cursor(dictionary=True)
    try:
        tag_type = request.args.get("tag_type")
        query = "SELECT tag_id, tag_name, tag_type FROM tags"
        params = []
        if tag_type:
            query += " WHERE tag_type = %s"
            params.append(tag_type)
        query += " ORDER BY tag_type, tag_name"
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a collection or add a recipe/tag relationship.
# Example: POST /collection/actions with {"resource": "collection", ...}
@collections.route("/actions", methods=["POST"])
def create_collection_action():
    database = get_db()
    cursor = database.cursor(dictionary=True)
    try:
        data = request.get_json(silent=True) or {}
        resource = data.get("resource")
        if resource == "collection":
            required = ["user_id", "collection_name"]
            query = """
                INSERT INTO collections (user_id, collection_name, description)
                VALUES (%s, %s, %s)
            """
            params = (data.get("user_id"), data.get("collection_name"),
                      data.get("description"))
            message = "Collection created successfully"
        elif resource == "collection_recipe":
            required = ["collection_id", "recipe_id"]
            query = """
                INSERT INTO collection_recipes (collection_id, recipe_id)
                VALUES (%s, %s)
            """
            params = (data.get("collection_id"), data.get("recipe_id"))
            message = "Recipe saved successfully"
        elif resource == "recipe_tag":
            required = ["recipe_id", "tag_id"]
            query = "INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (%s, %s)"
            params = (data.get("recipe_id"), data.get("tag_id"))
            message = "Tag assigned successfully"
        else:
            return jsonify(
                {"error": "resource must be collection, collection_recipe, or recipe_tag"}
            ), 400

        for field in required:
            if data.get(field) is None:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        cursor.execute(query, params)
        database.commit()
        return jsonify({"message": message, "id": cursor.lastrowid}), 201
    except Error as e:
        database.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update a collection's name or description.
# Example: PUT /collection/collections/1
@collections.route("/collections/<int:collection_id>", methods=["PUT"])
def update_collection(collection_id):
    database = get_db()
    cursor = database.cursor(dictionary=True)
    try:
        data = request.get_json(silent=True) or {}
        allowed_fields = ["collection_name", "description"]
        update_fields = [f"{field} = %s" for field in allowed_fields if field in data]
        params = [data[field] for field in allowed_fields if field in data]
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400
        params.append(collection_id)
        cursor.execute(
            f"UPDATE collections SET {', '.join(update_fields)} WHERE collection_id = %s",
            params,
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Collection not found"}), 404
        database.commit()
        return jsonify({"message": "Collection updated successfully"}), 200
    except Error as e:
        database.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a collection, saved recipe, or recipe-tag relationship.
# Example: DELETE /collection/actions?resource=collection_recipe&collection_id=1&recipe_id=2
@collections.route("/actions", methods=["DELETE"])
def delete_collection_action():
    database = get_db()
    cursor = database.cursor(dictionary=True)
    try:
        resource = request.args.get("resource")
        if resource == "collection":
            query = "DELETE FROM collections WHERE collection_id = %s"
            params = (request.args.get("collection_id"),)
        elif resource == "collection_recipe":
            query = """
                DELETE FROM collection_recipes
                WHERE collection_id = %s AND recipe_id = %s
            """
            params = (request.args.get("collection_id"), request.args.get("recipe_id"))
        elif resource == "recipe_tag":
            query = "DELETE FROM recipe_tags WHERE recipe_id = %s AND tag_id = %s"
            params = (request.args.get("recipe_id"), request.args.get("tag_id"))
        else:
            return jsonify({"error": "Invalid resource"}), 400

        if any(value is None for value in params):
            return jsonify({"error": "Required identifier is missing"}), 400
        cursor.execute(query, params)
        if cursor.rowcount == 0:
            return jsonify({"error": "Record not found"}), 404
        database.commit()
        return jsonify({"message": "Record deleted successfully"}), 200
    except Error as e:
        database.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
