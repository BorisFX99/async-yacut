import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from settings import Config

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(
        app,
        db,
        directory=os.path.join(app.instance_path, 'migrations'),
    )

    # Импорт моделей, чтобы SQLAlchemy их увидел
    from yacut import models  # noqa: F401
    from yacut import views
    from yacut import error_handlers
    from yacut import api_views

    app.register_blueprint(views.views)
    app.register_blueprint(error_handlers.bp_errors)
    app.register_blueprint(api_views.api_bp)

    return app