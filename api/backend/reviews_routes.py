"""General RecipeMe API routes for reviews, replies, reports, and audit logs."""

from flask import Blueprint, current_app, jsonify, request
from mysql.connector import Error

from backend.db_connection import get_db


reviews = Blueprint("reviews", __name__)


# Get reviews with optional recipe, user, and status filters.
# Example: GET /review/reviews?recipe_id=1&status=active
@reviews.route("/reviews", methods=["GET"])
def get_all_reviews():
    cursor = get_db().cursor(dictionary=True)
    try:
        recipe_id = request.args.get("recipe_id", type=int)
        user_id = request.args.get("user_id", type=int)
        status = request.args.get("status")
        query = """
            SELECT reviews.review_id, reviews.recipe_id, recipes.title,
                   reviews.user_id, users.full_name AS reviewer_name,
                   reviews.rating, reviews.review_text, reviews.status
            FROM reviews
            JOIN recipes ON reviews.recipe_id = recipes.recipe_id
            JOIN users ON reviews.user_id = users.user_id
            WHERE 1 = 1
        """
        params = []
        if recipe_id is not None:
            query += " AND reviews.recipe_id = %s"
            params.append(recipe_id)
        if user_id is not None:
            query += " AND reviews.user_id = %s"
            params.append(user_id)
        if status:
            query += " AND reviews.status = %s"
            params.append(status)
        query += " ORDER BY reviews.review_id DESC"
        cursor.execute(query, params)
        review_list = cursor.fetchall()
        current_app.logger.info(f"Retrieved {len(review_list)} reviews")
        return jsonify(review_list), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get one review and all of its replies.
# Example: GET /review/reviews/1
@reviews.route("/reviews/<int:review_id>", methods=["GET"])
def get_review(review_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT reviews.*, users.full_name AS reviewer_name,
                   recipes.title AS recipe_title
            FROM reviews
            JOIN users ON reviews.user_id = users.user_id
            JOIN recipes ON reviews.recipe_id = recipes.recipe_id
            WHERE reviews.review_id = %s
            """,
            (review_id,),
        )
        review = cursor.fetchone()
        if not review:
            return jsonify({"error": "Review not found"}), 404
        cursor.execute(
            """
            SELECT review_replies.reply_id, review_replies.user_id,
                   users.full_name AS reply_author, review_replies.reply_text,
                   review_replies.created_at
            FROM review_replies
            JOIN users ON review_replies.user_id = users.user_id
            WHERE review_replies.review_id = %s
            ORDER BY review_replies.created_at
            """,
            (review_id,),
        )
        review["replies"] = cursor.fetchall()
        return jsonify(review), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get reports with optional status and target-type filters.
# Example: GET /review/reports?status=open&target_type=review
@reviews.route("/reports", methods=["GET"])
def get_reports():
    cursor = get_db().cursor(dictionary=True)
    try:
        status = request.args.get("status")
        target_type = request.args.get("target_type")
        query = """
            SELECT reports.report_id, reports.reporter_user_id,
                   users.full_name AS reporter_name, reports.target_type,
                   reports.target_id, reports.reason, reports.status
            FROM reports
            JOIN users ON reports.reporter_user_id = users.user_id
            WHERE 1 = 1
        """
        params = []
        if status:
            query += " AND reports.status = %s"
            params.append(status)
        if target_type:
            query += " AND reports.target_type = %s"
            params.append(target_type)
        query += " ORDER BY reports.report_id DESC"
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get one report and the recipe or review it targets.
# Example: GET /review/reports/1
@reviews.route("/reports/<int:report_id>", methods=["GET"])
def get_report(report_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM reports WHERE report_id = %s", (report_id,))
        report = cursor.fetchone()
        if not report:
            return jsonify({"error": "Report not found"}), 404

        if report["target_type"] == "recipe":
            cursor.execute(
                "SELECT recipe_id, title, description, is_active FROM recipes WHERE recipe_id = %s",
                (report["target_id"],),
            )
        elif report["target_type"] == "review":
            cursor.execute(
                "SELECT review_id, rating, review_text, status FROM reviews WHERE review_id = %s",
                (report["target_id"],),
            )
        else:
            report["reported_content"] = None
            return jsonify(report), 200

        report["reported_content"] = cursor.fetchone()
        return jsonify(report), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get administrative audit-log records.
# Example: GET /review/audit-logs?admin_user_id=4&target_type=recipe
@reviews.route("/audit-logs", methods=["GET"])
def get_audit_logs():
    cursor = get_db().cursor(dictionary=True)
    try:
        admin_user_id = request.args.get("admin_user_id", type=int)
        target_type = request.args.get("target_type")
        query = """
            SELECT audit_logs.*, users.full_name AS admin_name
            FROM audit_logs
            JOIN users ON audit_logs.admin_user_id = users.user_id
            WHERE 1 = 1
        """
        params = []
        if admin_user_id is not None:
            query += " AND audit_logs.admin_user_id = %s"
            params.append(admin_user_id)
        if target_type:
            query += " AND audit_logs.target_type = %s"
            params.append(target_type)
        query += " ORDER BY audit_logs.action_time DESC"
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a review, reply, or report according to the resource field.
# Example: POST /review/actions with {"resource": "review", ...}
@reviews.route("/actions", methods=["POST"])
def create_review_action():
    database = get_db()
    cursor = database.cursor(dictionary=True)
    try:
        data = request.get_json(silent=True) or {}
        resource = data.get("resource")

        if resource == "review":
            required = ["recipe_id", "user_id", "rating", "review_text"]
            if data.get("rating") is not None and not 1 <= int(data["rating"]) <= 5:
                return jsonify({"error": "rating must be between 1 and 5"}), 400
            query = """
                INSERT INTO reviews
                    (recipe_id, user_id, rating, review_text, status)
                VALUES (%s, %s, %s, %s, 'active')
            """
            params = (data.get("recipe_id"), data.get("user_id"),
                      data.get("rating"), data.get("review_text"))
            message = "Review created successfully"
        elif resource == "reply":
            required = ["review_id", "user_id", "reply_text"]
            query = """
                INSERT INTO review_replies (review_id, user_id, reply_text)
                VALUES (%s, %s, %s)
            """
            params = (data.get("review_id"), data.get("user_id"),
                      data.get("reply_text"))
            message = "Reply created successfully"
        elif resource == "report":
            required = ["reporter_user_id", "target_type", "target_id", "reason"]
            if data.get("target_type") not in ("recipe", "review"):
                return jsonify({"error": "target_type must be recipe or review"}), 400
            query = """
                INSERT INTO reports
                    (reporter_user_id, target_type, target_id, reason, status)
                VALUES (%s, %s, %s, %s, 'open')
            """
            params = (data.get("reporter_user_id"), data.get("target_type"),
                      data.get("target_id"), data.get("reason"))
            message = "Report created successfully"
        else:
            return jsonify({"error": "resource must be review, reply, or report"}), 400

        for field in required:
            if data.get(field) is None:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute(query, params)
        database.commit()
        return jsonify({"message": message, "id": cursor.lastrowid}), 201
    except (Error, TypeError, ValueError) as e:
        database.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update a review, reply, or report using an allowlisted resource type.
# Example: PUT /review/content/report/1 with {"status": "resolved"}
@reviews.route("/content/<string:resource>/<int:resource_id>", methods=["PUT"])
def update_review_content(resource, resource_id):
    database = get_db()
    cursor = database.cursor(dictionary=True)
    try:
        data = request.get_json(silent=True) or {}
        definitions = {
            "review": ("reviews", "review_id", ["rating", "review_text", "status"]),
            "reply": ("review_replies", "reply_id", ["reply_text"]),
            "report": ("reports", "report_id", ["status"]),
        }
        if resource not in definitions:
            return jsonify({"error": "Invalid resource type"}), 400

        table_name, id_column, allowed_fields = definitions[resource]
        update_fields = [f"{field} = %s" for field in allowed_fields if field in data]
        params = [data[field] for field in allowed_fields if field in data]
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(resource_id)
        cursor.execute(
            f"UPDATE {table_name} SET {', '.join(update_fields)} WHERE {id_column} = %s",
            params,
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Record not found"}), 404

        if resource == "report" and data.get("admin_user_id") is not None:
            cursor.execute(
                """
                INSERT INTO audit_logs
                    (admin_user_id, action_type, target_type, target_id)
                VALUES (%s, %s, 'report', %s)
                """,
                (data["admin_user_id"], "Updated Report", resource_id),
            )

        database.commit()
        return jsonify({"message": "Record updated successfully"}), 200
    except Error as e:
        database.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a review, reply, or report.
# Example: DELETE /review/content/reply/2
@reviews.route("/content/<string:resource>/<int:resource_id>", methods=["DELETE"])
def delete_review_content(resource, resource_id):
    database = get_db()
    cursor = database.cursor(dictionary=True)
    try:
        definitions = {
            "review": ("reviews", "review_id"),
            "reply": ("review_replies", "reply_id"),
            "report": ("reports", "report_id"),
        }
        if resource not in definitions:
            return jsonify({"error": "Invalid resource type"}), 400
        table_name, id_column = definitions[resource]
        cursor.execute(
            f"DELETE FROM {table_name} WHERE {id_column} = %s",
            (resource_id,),
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Record not found"}), 404
        database.commit()
        return jsonify({"message": "Record deleted successfully"}), 200
    except Error as e:
        database.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

