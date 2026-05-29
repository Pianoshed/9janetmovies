from flask import Blueprint, jsonify, request
from app.models.series import Series

series_bp = Blueprint('series', __name__, url_prefix='/api')

@series_bp.route('/series')
def get_series():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    paginated = Series.query.order_by(Series.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'series': [s.to_dict() for s in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': paginated.page,
        'has_next': paginated.has_next,
        'has_prev': paginated.has_prev
    })

@series_bp.route('/series/<slug>')
def get_one_series(slug):
    s = Series.query.filter_by(slug=slug).first_or_404()
    return jsonify(s.to_dict())