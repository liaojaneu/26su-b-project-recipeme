from flask import Flask, jsonify
from dotenv import load_dotenv

import logging
import os

from backend.db_connection import init_app as init_db
from backend.users_routes import users
from backend.recipes_routes import recipes
from backend.collections_routes import collections
from backend.reviews_routes import reviews
from backend.admin_routes import admin


def create_app():
    app = Flask(__name__)

    app.logger.setLevel(logging.DEBUG)
    app.logger.info("RecipeMe API startup")

    load_dotenv()

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    app.config["MYSQL_DATABASE_USER"] = os.getenv(
        "DB_USER"
    ).strip()

    app.config["MYSQL_DATABASE_PASSWORD"] = os.getenv(
        "MYSQL_ROOT_PASSWORD"
    ).strip()

    app.config["MYSQL_DATABASE_HOST"] = os.getenv(
        "DB_HOST"
    ).strip()

    app.config["MYSQL_DATABASE_PORT"] = int(
        os.getenv("DB_PORT").strip()
    )

    app.config["MYSQL_DATABASE_DB"] = os.getenv(
        "DB_NAME"
    ).strip()

    app.logger.info(
        "create_app(): initializing database connection"
    )
    init_db(app)

    app.logger.info(
        "create_app(): registering RecipeMe blueprints"
    )

    app.register_blueprint(
        users,
        url_prefix="/user",
    )

    app.register_blueprint(
        recipes,
        url_prefix="/recipe",
    )

    app.register_blueprint(
        collections,
        url_prefix="/collection",
    )

    app.register_blueprint(
        reviews,
        url_prefix="/review",
    )

    app.register_blueprint(
        admin,
        url_prefix="/admin",
    )

    @app.route("/", methods=["GET"])
    def index():
        return jsonify(
            {
                "message": "RecipeMe API is running",
                "status": "healthy",
            }
        ), 200

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(
            {
                "service": "RecipeMe API",
                "status": "healthy",
            }
        ), 200

    app.logger.info("RecipeMe API created successfully")

    return app