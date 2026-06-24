from flask import Blueprint, jsonify, request
from app.models.movie import Movie
from app import db

genres_bp = Blueprint('genres', __name__, url_prefix='/api')

GENRES = [
    'Action', 'Thriller', 'Horror', 'Crime', 'Drama',
    'Family', 'Fantasy', 'Korean', 'Sci-Fi', 'Romance',
    'Animation', 'Chinese', 'War', 'History', 'Mystery',
    'Adventure', 'Nollywood'
]

# Map of known dirty values → canonical genre
GENRE_ALIASES = {
    'animation': 'Animation',
    'animated':  'Animation',
    'anime':     'Animation',
    'action':    'Action',
    'thriller':  'Thriller',
    'horror':    'Horror',
    'crime':     'Crime',
    'drama':     'Drama',
    'family':    'Family',
    'fantasy':   'Fantasy',
    'korean':    'Korean',
    'sci-fi':    'Sci-Fi',
    'scifi':     'Sci-Fi',
    'science fiction': 'Sci-Fi',
    'romance':   'Romance',
    'chinese':   'Chinese',
    'war':       'War',
    'history':   'History',
    'historical': 'History',
    'mystery':   'Mystery',
    'adventure': 'Adventure',
    'nollywood': 'Nollywood',
}


@genres_bp.route('/genres')
def get_genres():
    return jsonify(GENRES)


@genres_bp.route('/genres/<genre>')
def get_by_genre(genre):
    page = request.args.get('page', 1, type=int)

    # Exact case-insensitive match — no more partial/contains leakage
    movies = Movie.query.filter(
        db.func.lower(db.func.trim(Movie.genre)) == genre.strip().lower()
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


@genres_bp.route('/genres/normalize', methods=['POST'])
def normalize_genres():
    """
    Admin endpoint — POST /api/genres/normalize
    Cleans up dirty/inconsistent genre values in the DB.
    Call this once after deploying, then remove or protect with auth.
    """
    fixed = 0
    movies = Movie.query.all()

    for movie in movies:
        if not movie.genre:
            continue

        raw = movie.genre.strip().lower()
        canonical = GENRE_ALIASES.get(raw)

        if canonical and movie.genre != canonical:
            movie.genre = canonical
            fixed += 1

    db.session.commit()
    return jsonify({'status': 'ok', 'fixed': fixed})


@genres_bp.route('/genres/audit')
def audit_genres():
    """
    Dev helper — GET /api/genres/audit
    Returns all distinct genre values and counts so you can
    spot dirty data before running /normalize.
    """
    from sqlalchemy import func
    rows = (
        db.session.query(Movie.genre, func.count(Movie.id))
        .group_by(Movie.genre)
        .order_by(Movie.genre)
        .all()
    )
    return jsonify([{'genre': g, 'count': c} for g, c in rows])