from flask import Blueprint, jsonify, request
from app.models.movie import Movie

movies_bp = Blueprint('movies', __name__, url_prefix='/api')

@movies_bp.route('/movies')
def get_movies():
    page  = request.args.get('page', 1, type=int)
    genre = request.args.get('genre', None)

    query = Movie.query
    if genre:
        query = query.filter(Movie.genre.ilike(f'%{genre}%'))

    movies = query.order_by(Movie.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return jsonify({
        'movies':  [m.to_dict() for m in movies.items],
        'total':   movies.total,
        'pages':   movies.pages,
        'current': movies.page
    })

@movies_bp.route('/movies/<slug>')
def get_movie(slug):
    movie = Movie.query.filter_by(slug=slug).first_or_404()
    return jsonify(movie.to_dict())