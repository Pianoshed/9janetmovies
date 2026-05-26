from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, login_user, logout_user, current_user
from flask import redirect, url_for, request, flash, render_template_string
from app.models.movie import Movie
from app.models.download_link import DownloadLink
from app.models.series import Series
from app.models.episode import Episode
from app.models.admin_user import AdminUser
from app import db
import re

login_manager = LoginManager()

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

# ── LOGIN PAGE TEMPLATE ──────────────────────────────────────
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>9janetmovies Admin Login</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: Arial, sans-serif;
            background: #001f66;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .login-box {
            background: #fff;
            padding: 40px;
            border-radius: 6px;
            width: 100%;
            max-width: 380px;
            border-top: 5px solid #cc0000;
        }
        h2 {
            text-align: center;
            margin-bottom: 6px;
            color: #001f66;
            font-size: 22px;
        }
        .subtitle {
            text-align: center;
            color: #777;
            font-size: 13px;
            margin-bottom: 24px;
        }
        label {
            display: block;
            font-size: 13px;
            font-weight: bold;
            margin-bottom: 4px;
            color: #333;
        }
        input[type=text], input[type=password] {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            margin-bottom: 16px;
        }
        button {
            width: 100%;
            padding: 11px;
            background: #cc0000;
            color: #fff;
            border: none;
            border-radius: 4px;
            font-size: 15px;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover { background: #990000; }
        .error {
            background: #ffe6e6;
            color: #cc0000;
            padding: 10px;
            border-radius: 4px;
            font-size: 13px;
            margin-bottom: 16px;
            border: 1px solid #ffcccc;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>9janet<span style="color:#cc0000">movies</span></h2>
        <p class="subtitle">Admin Panel — Sign In</p>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <label>Username</label>
            <input type="text" name="username" required autofocus />
            <label>Password</label>
            <input type="password" name="password" required />
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
"""

# ── PROTECTED INDEX ──────────────────────────────────────────
class SecureAdminIndex(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('admin_login'))
        return super().index()

# ── PROTECTED MODEL VIEWS ────────────────────────────────────
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))

class MovieAdmin(SecureModelView):
    column_list = ['title', 'genre', 'year', 'badge', 'is_trending', 'created_at']
    column_searchable_list = ['title', 'genre']
    column_filters = ['genre', 'year', 'is_trending', 'badge']
    form_excluded_columns = ['created_at', 'links']
    can_export = True
    page_size = 20

    def on_model_change(self, form, model, is_created):
        if not model.slug:
            model.slug = slugify(model.title)

class DownloadLinkAdmin(SecureModelView):
    column_list = ['movie', 'label', 'host', 'url']
    column_searchable_list = ['label', 'host']
    column_filters = ['host', 'label']
    page_size = 20

class SeriesAdmin(SecureModelView):
    column_list = ['title', 'genre', 'created_at']
    column_searchable_list = ['title', 'genre']
    form_excluded_columns = ['created_at', 'episodes']
    page_size = 20

    def on_model_change(self, form, model, is_created):
        if not model.slug:
            model.slug = slugify(model.title)

class EpisodeAdmin(SecureModelView):
    column_list = ['series', 'season', 'episode', 'title', 'host']
    column_filters = ['season', 'host']
    page_size = 20

# ── INIT ─────────────────────────────────────────────────────
def init_admin(app):
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))

    # Login route
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if current_user.is_authenticated:
            return redirect('/admin')
        error = None
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = AdminUser.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect('/admin')
            error = 'Invalid username or password.'
        return render_template_string(LOGIN_TEMPLATE, error=error)

    # Logout route
    @app.route('/admin/logout')
    def admin_logout():
        logout_user()
        return redirect('/admin/login')

    admin = Admin(
        app,
        name='9janetmovies Admin',
        index_view=SecureAdminIndex()
    )
    admin.add_view(MovieAdmin(Movie, db.session, name='Movies', endpoint='admin_movies'))
    admin.add_view(DownloadLinkAdmin(DownloadLink, db.session, name='Download Links', endpoint='admin_links'))
    admin.add_view(SeriesAdmin(Series, db.session, name='Series', endpoint='admin_series'))
    admin.add_view(EpisodeAdmin(Episode, db.session, name='Episodes', endpoint='admin_episodes'))

    return admin