import os
from flask import Flask, app        # ← remove the duplicate 'app, app' imports
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=[
        "http://localhost:3000",
        os.getenv("https://ninejamoviesnet1.onrender.com", ""),
    ])

    from app.models.movie import Movie
    from app.models.download_link import DownloadLink
    from app.models.series import Series
    from app.models.episode import Episode
    from app.models.admin_user import AdminUser

    from app.routes.crawler import crawler_bp
    app.register_blueprint(crawler_bp)
    
    from app.routes.movies import movies_bp
    from app.routes.series import series_bp
    from app.routes.search import search_bp
    from app.routes.genres import genres_bp
    from app.routes.trending import trending_bp
    app.register_blueprint(movies_bp)
    app.register_blueprint(series_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(genres_bp)
    app.register_blueprint(trending_bp)

    from app.admin.views import init_admin
    init_admin(app)

    return app