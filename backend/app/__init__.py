import os
from flask import Flask, request, jsonify
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logging.getLogger('flask-limiter').setLevel(logging.CRITICAL)
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY")

def get_request_identifier():
    # Internal Next.js server calls are exempt from rate limiting
    if INTERNAL_API_KEY and request.headers.get("X-Internal-Key") == INTERNAL_API_KEY:
        return None  # returning None skips rate limiting for this request
    return get_remote_address()

limiter = Limiter(
    key_func=get_request_identifier,
    default_limits=["60 per minute"],
    storage_uri=os.environ.get("REDIS_URL", "memory://")
)

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    app.config['MAIL_SERVER']         = os.environ.get('MAIL_SERVER', 'smtppro.zoho.com')
    app.config['MAIL_PORT']           = int(os.environ.get('MAIL_PORT', 465))
    app.config['MAIL_USE_SSL']        = True
    app.config['MAIL_USE_TLS']        = False
    app.config['MAIL_USERNAME']       = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD']       = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    limiter.init_app(app)

    CORS(app, origins=[
        "http://localhost:3000",
        "https://9janetmovies.com.ng",
        "https://ninejamoviesnet1.onrender.com",
        os.getenv("FRONTEND_URL", ""),
    ])

    from app.models.movie import Movie
    from app.models.download_link import DownloadLink
    from app.models.series import Series
    from app.models.episode import Episode
    from app.models.admin_user import AdminUser
    from app.models.blog_post import BlogPost

    with app.app_context():
        db.create_all()

    from app.routes.blog import blog_bp
    from app.routes.crawler import crawler_bp
    from app.routes.movies import movies_bp
    from app.routes.series import series_bp
    from app.routes.search import search_bp
    from app.routes.genres import genres_bp
    from app.routes.trending import trending_bp
    from app.routes.mail import mail_bp
    from app.routes.rss import rss_bp  

    app.register_blueprint(blog_bp)
    app.register_blueprint(crawler_bp)
    app.register_blueprint(movies_bp)
    app.register_blueprint(series_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(genres_bp)
    app.register_blueprint(trending_bp)
    app.register_blueprint(mail_bp)
    app.register_blueprint(rss_bp)

    from app.admin.views import init_admin
    init_admin(app)

    return app