from flask import Blueprint, jsonify
from app.models.movie import Movie

trending_bp = Blueprint('trending', __name__, url_prefix='/api')

@trending_bp.route('/trending')
def get_trending():
    # Try is_trending=True with TMDB posters first
    movies = Movie.query.filter(
        Movie.is_trending == True,
        Movie.poster_url.isnot(None),
        Movie.poster_url != '',
        Movie.poster_url.like('%image.tmdb.org%'),
    ).order_by(Movie.created_at.desc()).limit(10).all()

    # Fallback: newest movies with TMDB posters
    if not movies:
        movies = Movie.query.filter(
            Movie.poster_url.isnot(None),
            Movie.poster_url != '',
            Movie.poster_url.like('%image.tmdb.org%'),
        ).order_by(Movie.created_at.desc()).limit(10).all()

    return jsonify([m.to_dict() for m in movies])