from flask import Blueprint, jsonify, request
from app.models.movie import Movie

genres_bp = Blueprint('genres', __name__, url_prefix='/api')

GENRES = [
    'Action','Thriller','Horror','Crime','Drama',
    'Family','Fantasy','Korean','Sci-Fi','Romance',
    'Animation','Chinese','War','History','Mystery',
    'Adventure','Nollywood'
]

@genres_bp.route('/genres')
def get_genres():
    return jsonify(GENRES)

@genres_bp.route('/genres/<genre>')
def get_by_genre(genre):
    page = request.args.get('page', 1, type=int)
    movies = Movie.query.filter(
        Movie.genre.ilike(f'%{genre}%')
    ).order_by(Movie.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return jsonify({
        'genre':   genre,
        'movies':  [m.to_dict() for m in movies.items],
        'total':   movies.total,
        'pages':   movies.pages,
        'current': movies.page
    })