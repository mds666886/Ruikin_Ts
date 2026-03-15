import os
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from .api.routes import api_bp
from .models.db import db


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///yanxi_pro.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=30 * 1024 * 1024,
        UPLOAD_DIR=os.getenv("UPLOAD_DIR", "uploads"),
    )

    if test_config:
        app.config.update(test_config)

    Path(app.config["UPLOAD_DIR"]).mkdir(parents=True, exist_ok=True)

    CORS(app)
    db.init_app(app)

    @app.errorhandler(413)
    def file_too_large(_):
        return jsonify({"code": 1, "message": "文件过大（>30MB）", "data": {}}), 413

    @app.errorhandler(Exception)
    def handle_exception(err):
        if app.config.get("TESTING"):
            raise err
        return jsonify({"code": 1, "message": f"服务异常: {type(err).__name__}", "data": {}}), 500

    with app.app_context():
        db.create_all()

    app.register_blueprint(api_bp, url_prefix="/api")
    return app
