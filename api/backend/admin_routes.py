"""Flask routes for RecipeMe's system-administrator features.

Register this Blueprint in the Flask application with a URL prefix:

    from backend.admin_routes import admin
    app.register_blueprint(admin, url_prefix="/admin")

The routes in this file support the David Lopez administrator persona and use
the users, recipes, reviews, reports, and audit_logs tables.
"""

from flask import Blueprint, current_app, jsonify, request
from mysql.connector import Error

from backend.db_connection import get_db


# Create a Blueprint for RecipeMe administrator routes.
admin = Blueprint("admin", __name__)


# Get a summary of records that may require administrator attention.
# Example: GET /admin/dashboard-summary
@admin.route("/dashboard-summary", methods=["GET"])
def get_dashboard_summary():
    cursor = get_db().cursor(dictionary=True)

    try:
        current_app.logger.info("GET /admin/dashboard-summary")

        cursor.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM users
                 WHERE account_status = 'suspended') AS suspended_users,
                (SELECT COUNT(*) FROM recipes
                 WHERE is_active = FALSE) AS archived_recipes,
                (SELECT COUNT(*) FROM reviews
                 WHERE status = 'hidden') AS hidden_reviews,
                (SELECT COUNT(*) FROM reports
                 WHERE status = 'open') AS open_reports
            """
        )

        return jsonify(cursor.fetchone()), 200
    except Error as e:
        current_app.logger.error(
            f"Database error in get_dashboard_summary: {e}"
        )
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get all users with optional filtering by role and account status.
# Example: GET /admin/users?role=creator&account_status=active
@admin.route("/users", methods=["GET"])
def get_all_users():
    cursor = get_db().cursor(dictionary=True)

    try:
        current_app.logger.info("GET /admin/users")

        role = request.args.get("role")
        account_status = request.args.get("account_status")

        query = """
            SELECT user_id, full_name, email, role, account_status, created_at
            FROM users
            WHERE 1 = 1
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
        users = cursor.fetchall()

        current_app.logger.info(f"Retrieved {len(users)} users")
        return jsonify(users), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_all_users: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get one user's profile and the number of recipes and reviews they created.
# Example: GET /admin/users/3
@admin.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    cursor = get_db().cursor(dictionary=True)

    try:
        current_app.logger.info(f"GET /admin/users/{user_id}")

        cursor.execute(
            """
            SELECT user_id, full_name, email, role, account_status, created_at
            FROM users
            WHERE user_id = %s
            """,
            (user_id,),
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        cursor.execute(
            "SELECT COUNT(*) AS recipe_count FROM recipes WHERE creator_id = %s",
            (user_id,),
        )
        user["recipe_count"] = cursor.fetchone()["recipe_count"]

        cursor.execute(
            "SELECT COUNT(*) AS review_count FROM reviews WHERE user_id = %s",
            (user_id,),
        )
        user["review_count"] = cursor.fetchone()["review_count"]

        return jsonify(user), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_user: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get reports with optional filtering by status and target type.
# Example: GET /admin/reports?status=open&target_type=recipe
@admin.route("/reports", methods=["GET"])
def get_all_reports():
    cursor = get_db().cursor(dictionary=True)

    try:
        current_app.logger.info("GET /admin/reports")

        status = request.args.get("status")
        target_type = request.args.get("target_type")

        query = """
            SELECT reports.report_id,
                   reports.reporter_user_id,
                   users.full_name AS reporter_name,
                   reports.target_type,
                   reports.target_id,
                   reports.reason,
                   reports.status
            FROM reports
            JOIN users
                ON reports.reporter_user_id = users.user_id
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
        reports = cursor.fetchall()

        current_app.logger.info(f"Retrieved {len(reports)} reports")
        return jsonify(reports), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_all_reports: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get one report and information about its reported recipe or review.
# Example: GET /admin/reports/1
@admin.route("/reports/<int:report_id>", methods=["GET"])
def get_report(report_id):
    cursor = get_db().cursor(dictionary=True)

    try:
        current_app.logger.info(f"GET /admin/reports/{report_id}")

        cursor.execute(
            """
            SELECT reports.report_id,
                   reports.reporter_user_id,
                   users.full_name AS reporter_name,
                   reports.target_type,
                   reports.target_id,
                   reports.reason,
                   reports.status
            FROM reports
            JOIN users
                ON reports.reporter_user_id = users.user_id
            WHERE reports.report_id = %s
            """,
            (report_id,),
        )
        report = cursor.fetchone()

        if not report:
            return jsonify({"error": "Report not found"}), 404

        if report["target_type"] == "recipe":
            cursor.execute(
                """
                SELECT recipe_id, creator_id, title, description, is_active
                FROM recipes
                WHERE recipe_id = %s
                """,
                (report["target_id"],),
            )
            report["reported_content"] = cursor.fetchone()
        elif report["target_type"] == "review":
            cursor.execute(
                """
                SELECT review_id, recipe_id, user_id, rating, review_text, status
                FROM reviews
                WHERE review_id = %s
                """,
                (report["target_id"],),
            )
            report["reported_content"] = cursor.fetchone()
        else:
            report["reported_content"] = None

        return jsonify(report), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_report: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Submit a report about a recipe or review.
# Required fields: reporter_user_id, target_type, target_id, reason
# Example: POST /admin/reports with a JSON body
@admin.route("/reports", methods=["POST"])
def create_report():
    database = get_db()
    cursor = database.cursor(dictionary=True)

    try:
        current_app.logger.info("POST /admin/reports")

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "A JSON request body is required"}), 400

        required_fields = [
            "reporter_user_id",
            "target_type",
            "target_id",
            "reason",
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        if data["target_type"] not in ("recipe", "review"):
            return jsonify(
                {"error": "target_type must be 'recipe' or 'review'"}
            ), 400

        target_queries = {
            "recipe": "SELECT recipe_id FROM recipes WHERE recipe_id = %s",
            "review": "SELECT review_id FROM reviews WHERE review_id = %s",
        }
        cursor.execute(
            target_queries[data["target_type"]],
            (data["target_id"],),
        )
        if not cursor.fetchone():
            return jsonify({"error": "Reported content not found"}), 404

        cursor.execute(
            """
            INSERT INTO reports
                (reporter_user_id, target_type, target_id, reason, status)
            VALUES
                (%s, %s, %s, %s, 'open')
            """,
            (
                data["reporter_user_id"],
                data["target_type"],
                data["target_id"],
                data["reason"],
            ),
        )
        database.commit()

        return jsonify(
            {
                "message": "Report created successfully",
                "report_id": cursor.lastrowid,
            }
        ), 201
    except Error as e:
        database.rollback()
        current_app.logger.error(f"Database error in create_report: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Perform one moderation action and record it in the audit log.
# Valid target types and actions:
#   user: suspend or reactivate
#   recipe: archive or restore
#   review: hide or show
#   report: resolve or reopen
# Example: PUT /admin/moderation/recipe/2 with {"admin_user_id": 4,
#                                                   "action": "archive"}
@admin.route("/moderation/<string:target_type>/<int:target_id>", methods=["PUT"])
def moderate_content(target_type, target_id):
    database = get_db()
    cursor = database.cursor(dictionary=True)

    try:
        current_app.logger.info(
            f"PUT /admin/moderation/{target_type}/{target_id}"
        )

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "A JSON request body is required"}), 400

        if "admin_user_id" not in data or "action" not in data:
            return jsonify(
                {"error": "admin_user_id and action are required"}
            ), 400

        action = str(data["action"]).lower()

        # Every SQL fragment below is selected from this fixed allowlist.
        # No table name, column name, or SQL value comes directly from the user.
        moderation_actions = {
            ("user", "suspend"): (
                "users",
                "user_id",
                "account_status",
                "suspended",
                "Suspended User",
            ),
            ("user", "reactivate"): (
                "users",
                "user_id",
                "account_status",
                "active",
                "Reactivated User",
            ),
            ("recipe", "archive"): (
                "recipes",
                "recipe_id",
                "is_active",
                False,
                "Archived Recipe",
            ),
            ("recipe", "restore"): (
                "recipes",
                "recipe_id",
                "is_active",
                True,
                "Restored Recipe",
            ),
            ("review", "hide"): (
                "reviews",
                "review_id",
                "status",
                "hidden",
                "Hid Review",
            ),
            ("review", "show"): (
                "reviews",
                "review_id",
                "status",
                "active",
                "Restored Review",
            ),
            ("report", "resolve"): (
                "reports",
                "report_id",
                "status",
                "resolved",
                "Resolved Report",
            ),
            ("report", "reopen"): (
                "reports",
                "report_id",
                "status",
                "open",
                "Reopened Report",
            ),
        }

        action_details = moderation_actions.get((target_type, action))
        if not action_details:
            return jsonify(
                {
                    "error": "Invalid target_type and action combination",
                    "valid_actions": {
                        "user": ["suspend", "reactivate"],
                        "recipe": ["archive", "restore"],
                        "review": ["hide", "show"],
                        "report": ["resolve", "reopen"],
                    },
                }
            ), 400

        table_name, id_column, status_column, new_value, audit_action = (
            action_details
        )

        cursor.execute(
            f"SELECT {id_column} FROM {table_name} WHERE {id_column} = %s",
            (target_id,),
        )
        if not cursor.fetchone():
            return jsonify({"error": f"{target_type.title()} not found"}), 404

        cursor.execute(
            f"UPDATE {table_name} SET {status_column} = %s "
            f"WHERE {id_column} = %s",
            (new_value, target_id),
        )

        cursor.execute(
            """
            INSERT INTO audit_logs
                (admin_user_id, action_type, target_type, target_id)
            VALUES
                (%s, %s, %s, %s)
            """,
            (data["admin_user_id"], audit_action, target_type, target_id),
        )

        database.commit()
        return jsonify(
            {
                "message": f"{audit_action} successfully",
                "target_type": target_type,
                "target_id": target_id,
            }
        ), 200
    except Error as e:
        database.rollback()
        current_app.logger.error(f"Database error in moderate_content: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a report record.
# Example: DELETE /admin/reports/8
@admin.route("/reports/<int:report_id>", methods=["DELETE"])
def delete_report(report_id):
    database = get_db()
    cursor = database.cursor(dictionary=True)

    try:
        current_app.logger.info(f"DELETE /admin/reports/{report_id}")

        cursor.execute(
            "SELECT report_id FROM reports WHERE report_id = %s",
            (report_id,),
        )
        if not cursor.fetchone():
            return jsonify({"error": "Report not found"}), 404

        cursor.execute("DELETE FROM reports WHERE report_id = %s", (report_id,))
        database.commit()

        return jsonify({"message": "Report deleted successfully"}), 200
    except Error as e:
        database.rollback()
        current_app.logger.error(f"Database error in delete_report: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get administrator audit-log entries with optional filters.
# Example: GET /admin/audit-logs?admin_user_id=4&target_type=recipe
@admin.route("/audit-logs", methods=["GET"])
def get_audit_logs():
    cursor = get_db().cursor(dictionary=True)

    try:
        current_app.logger.info("GET /admin/audit-logs")

        admin_user_id = request.args.get("admin_user_id", type=int)
        target_type = request.args.get("target_type")

        query = """
            SELECT audit_logs.audit_id,
                   audit_logs.admin_user_id,
                   users.full_name AS admin_name,
                   audit_logs.action_type,
                   audit_logs.target_type,
                   audit_logs.target_id,
                   audit_logs.action_time
            FROM audit_logs
            JOIN users
                ON audit_logs.admin_user_id = users.user_id
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
        audit_logs = cursor.fetchall()

        current_app.logger.info(f"Retrieved {len(audit_logs)} audit log entries")
        return jsonify(audit_logs), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_audit_logs: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
