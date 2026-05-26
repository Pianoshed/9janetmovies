from flask import Blueprint, jsonify, request
from app.models.movie import Movie

search_bp = Blueprint('search', __name__, url_prefix='/api')

@search_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    results = Movie.query.filter(
        Movie.title.ilike(f'%{q}%')
    ).limit(20).all()
    return jsonify([m.to_dict() for m in results])