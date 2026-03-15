from flask import Flask
from flask_cors import CORS

from .models.db import db
from .api.routes import api_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///yanxi_pro.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

    CORS(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(api_bp, url_prefix="/api")
    return app
