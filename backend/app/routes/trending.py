from flask import Blueprint, jsonify
from app.models.movie import Movie

trending_bp = Blueprint('trending', __name__, url_prefix='/api')

@trending_bp.route('/trending')
def get_trending():
    movies = Movie.query.filter_by(
        is_trending=True
    ).order_by(Movie.created_at.desc()).limit(5).all()
    return jsonify([m.to_dict() for m in movies])