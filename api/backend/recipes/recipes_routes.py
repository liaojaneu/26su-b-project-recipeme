"""General RecipeMe API routes for recipe-related database resources."""

from flask import Blueprint, current_app, jsonify, request
from mysql.connector import Error

from backend.db_connection import get_db


recipes = Blueprint("recipes", __name__)


# Get active recipes with optional filters.
# Example: GET /recipe/recipes?ingredient=Garlic&tag=Gluten-Free&difficulty=Easy
@recipes.route("/recipes", methods=["GET"])
def get_all_recipes():
    cursor = get_db().cursor(dictionary=True)
    try:
        ingredient = request.args.get("ingredient")
        tag = request.args.get("tag")
        difficulty = request.args.get("difficulty")
        creator_id = request.args.get("creator_id", type=int)
        max_minutes = request.args.get("max_minutes", type=int)

        query = """
            SELECT DISTINCT recipes.recipe_id, recipes.creator_id,
                   users.full_name AS creator_name, recipes.title,
                   recipes.description, recipes.prep_minutes,
                   recipes.cook_minutes, recipes.difficulty,
                   recipes.media_url, recipes.is_active
            FROM recipes
            JOIN users ON recipes.creator_id = users.user_id
            LEFT JOIN recipe_ingredients
                ON recipes.recipe_id = recipe_ingredients.recipe_id
            LEFT JOIN ingredients
                ON recipe_ingredients.ingredient_id = ingredients.ingredient_id
            LEFT JOIN recipe_tags
                ON recipes.recipe_id = recipe_tags.recipe_id
            LEFT JOIN tags ON recipe_tags.tag_id = tags.tag_id
            WHERE recipes.is_active = TRUE
        """
        params = []

        if ingredient:
            query += " AND ingredients.ingredient_name LIKE %s"
            params.append(f"%{ingredient}%")
        if tag:
            query += " AND tags.tag_name = %s"
            params.append(tag)
        if difficulty:
            query += " AND recipes.difficulty = %s"
            params.append(difficulty)
        if creator_id is not None:
            query += " AND recipes.creator_id = %s"
            params.append(creator_id)
        if max_minutes is not None:
            query += " AND recipes.prep_minutes + recipes.cook_minutes <= %s"
            params.append(max_minutes)

        query += " ORDER BY recipes.title"
        cursor.execute(query, params)
        recipe_list = cursor.fetchall()
        current_app.logger.info(f"Retrieved {len(recipe_list)} recipes")
        return jsonify(recipe_list), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_all_recipes: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get one recipe and all closely related information.
# Example: GET /recipe/recipes/1
@recipes.route("/recipes/<int:recipe_id>", methods=["GET"])
def get_recipe(recipe_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT recipes.*, users.full_name AS creator_name
            FROM recipes
            JOIN users ON recipes.creator_id = users.user_id
            WHERE recipes.recipe_id = %s
            """,
            (recipe_id,),
        )
        recipe = cursor.fetchone()
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404

        cursor.execute(
            """
            SELECT ingredients.ingredient_id, ingredients.ingredient_name,
                   recipe_ingredients.quantity, recipe_ingredients.unit
            FROM recipe_ingredients
            JOIN ingredients
                ON recipe_ingredients.ingredient_id = ingredients.ingredient_id
            WHERE recipe_ingredients.recipe_id = %s
            ORDER BY ingredients.ingredient_name
            """,
            (recipe_id,),
        )
        recipe["ingredients"] = cursor.fetchall()

        cursor.execute(
            """
            SELECT step_id, step_number, instruction
            FROM recipe_steps
            WHERE recipe_id = %s
            ORDER BY step_number
            """,
            (recipe_id,),
        )
        recipe["steps"] = cursor.fetchall()

        cursor.execute(
            """
            SELECT tags.tag_id, tags.tag_name, tags.tag_type
            FROM recipe_tags
            JOIN tags ON recipe_tags.tag_id = tags.tag_id
            WHERE recipe_tags.recipe_id = %s
            """,
            (recipe_id,),
        )
        recipe["tags"] = cursor.fetchall()

        cursor.execute(
            """
            SELECT link_id, platform, url
            FROM external_links
            WHERE recipe_id = %s
            """,
            (recipe_id,),
        )
        recipe["external_links"] = cursor.fetchall()
        return jsonify(recipe), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get ingredients belonging to one recipe.
# Example: GET /recipe/recipes/1/ingredients
@recipes.route("/recipes/<int:recipe_id>/ingredients", methods=["GET"])
def get_recipe_ingredients(recipe_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT ingredients.ingredient_id, ingredients.ingredient_name,
                   recipe_ingredients.quantity, recipe_ingredients.unit
            FROM recipe_ingredients
            JOIN ingredients
                ON recipe_ingredients.ingredient_id = ingredients.ingredient_id
            WHERE recipe_ingredients.recipe_id = %s
            """,
            (recipe_id,),
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get steps belonging to one recipe.
# Example: GET /recipe/recipes/1/steps
@recipes.route("/recipes/<int:recipe_id>/steps", methods=["GET"])
def get_recipe_steps(recipe_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT step_id, step_number, instruction
            FROM recipe_steps WHERE recipe_id = %s ORDER BY step_number
            """,
            (recipe_id,),
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get engagement totals for one recipe.
# Example: GET /recipe/recipes/1/engagement
@recipes.route("/recipes/<int:recipe_id>/engagement", methods=["GET"])
def get_recipe_engagement(recipe_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT recipes.recipe_id, recipes.title,
                   COUNT(DISTINCT collection_recipes.collection_id) AS saves,
                   COUNT(DISTINCT CASE WHEN reviews.status = 'active'
                                       THEN reviews.review_id END) AS reviews,
                   ROUND(AVG(CASE WHEN reviews.status = 'active'
                                  THEN reviews.rating END), 2) AS average_rating
            FROM recipes
            LEFT JOIN collection_recipes
                ON recipes.recipe_id = collection_recipes.recipe_id
            LEFT JOIN reviews ON recipes.recipe_id = reviews.recipe_id
            WHERE recipes.recipe_id = %s
            GROUP BY recipes.recipe_id, recipes.title
            """,
            (recipe_id,),
        )
        engagement = cursor.fetchone()
        if not engagement:
            return jsonify({"error": "Recipe not found"}), 404
        return jsonify(engagement), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a recipe. Optional arrays may include steps, ingredients, tag_ids,
# and external_links.
# Example: POST /recipe/recipes
@recipes.route("/recipes", methods=["POST"])
def create_recipe():
    database = get_db()
    cursor = database.cursor(dictionary=True)
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "A JSON request body is required"}), 400

        required_fields = ["creator_id", "title", "prep_minutes", "cook_minutes"]
        for field in required_fields:
            if data.get(field) is None:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute(
            """
            INSERT INTO recipes
                (creator_id, title, description, prep_minutes, cook_minutes,
                 difficulty, media_url, cooking_tips, substitutions,
                 serving_suggestions, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            """,
            (
                data["creator_id"], data["title"], data.get("description"),
                data["prep_minutes"], data["cook_minutes"],
                data.get("difficulty"), data.get("media_url"),
                data.get("cooking_tips"), data.get("substitutions"),
                data.get("serving_suggestions"),
            ),
        )
        recipe_id = cursor.lastrowid

        for step in data.get("steps", []):
            cursor.execute(
                """
                INSERT INTO recipe_steps (recipe_id, step_number, instruction)
                VALUES (%s, %s, %s)
                """,
                (recipe_id, step["step_number"], step["instruction"]),
            )
        for ingredient in data.get("ingredients", []):
            cursor.execute(
                """
                INSERT INTO recipe_ingredients
                    (recipe_id, ingredient_id, quantity, unit)
                VALUES (%s, %s, %s, %s)
                """,
                (recipe_id, ingredient["ingredient_id"],
                 ingredient.get("quantity"), ingredient.get("unit")),
            )
        for tag_id in data.get("tag_ids", []):
            cursor.execute(
                "INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (%s, %s)",
                (recipe_id, tag_id),
            )
        for link in data.get("external_links", []):
            cursor.execute(
                """
                INSERT INTO external_links (recipe_id, platform, url)
                VALUES (%s, %s, %s)
                """,
                (recipe_id, link["platform"], link["url"]),
            )

        database.commit()
        return jsonify(
            {"message": "Recipe created successfully", "recipe_id": recipe_id}
        ), 201
    except (Error, KeyError, TypeError) as e:
        database.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update any provided recipe fields, including is_active for archive/restore.
# Example: PUT /recipe/recipes/1
@recipes.route("/recipes/<int:recipe_id>", methods=["PUT"])
def update_recipe(recipe_id):
    database = get_db()
    cursor = database.cursor(dictionary=True)
    try:
        data = request.get_json(silent=True) or {}
        cursor.execute("SELECT recipe_id FROM recipes WHERE recipe_id = %s", (recipe_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Recipe not found"}), 404

        allowed_fields = [
            "title", "description", "prep_minutes", "cook_minutes",
            "difficulty", "media_url", "cooking_tips", "substitutions",
            "serving_suggestions", "is_active",
        ]
        update_fields = [f"{field} = %s" for field in allowed_fields if field in data]
        params = [data[field] for field in allowed_fields if field in data]
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(recipe_id)
        cursor.execute(
            f"UPDATE recipes SET {', '.join(update_fields)} WHERE recipe_id = %s",
            params,
        )
        database.commit()
        return jsonify({"message": "Recipe updated successfully"}), 200
    except Error as e:
        database.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Permanently delete a recipe. Use PUT is_active=false when archiving is desired.
# Example: DELETE /recipe/recipes/1
@recipes.route("/recipes/<int:recipe_id>", methods=["DELETE"])
def delete_recipe(recipe_id):
    database = get_db()
    cursor = database.cursor(dictionary=True)
    try:
        cursor.execute("DELETE FROM recipes WHERE recipe_id = %s", (recipe_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Recipe not found"}), 404
        database.commit()
        return jsonify({"message": "Recipe deleted successfully"}), 200
    except Error as e:
        database.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

