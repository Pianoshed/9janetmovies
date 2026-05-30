import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # Mail config
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

    app.register_blueprint(blog_bp)
    app.register_blueprint(crawler_bp)
    app.register_blueprint(movies_bp)
    app.register_blueprint(series_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(genres_bp)
    app.register_blueprint(trending_bp)
    app.register_blueprint(mail_bp)

    from app.admin.views import init_admin
    init_admin(app)

    return app