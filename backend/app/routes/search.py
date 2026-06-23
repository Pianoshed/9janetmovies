from flask import Blueprint, jsonify, request
from app.models.movie import Movie
from app.models.series import Series
from sqlalchemy import or_

search_bp = Blueprint('search', __name__, url_prefix='/api')

@search_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    pattern = f'%{q}%'

    movies = Movie.query.filter(Movie.title.ilike(pattern)).limit(10).all()
    series = Series.query.filter(Series.title.ilike(pattern)).limit(10).all()

    results = (
        [{'type': 'movie',  **m.to_dict()} for m in movies] +
        [{'type': 'series', **s.to_dict()} for s in series]
    )

    # sort by relevance: exact prefix matches first, then alphabetical
    q_lower = q.lower()
    results.sort(key=lambda r: (
        0 if r['title'].lower().startswith(q_lower) else 1,
        r['title'].lower()
    ))

    return jsonify(results[:20])