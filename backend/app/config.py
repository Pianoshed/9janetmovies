import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    APP_NAME = '9janetmovies'
    SECRET_KEY = os.getenv('SECRET_KEY', '9janetmovies-secret-2026')
    FLASK_ADMIN_SWATCH = 'cerulean'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    _db_url = os.getenv('DATABASE_URL', 'postgresql://localhost/9janetmovies')

    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url