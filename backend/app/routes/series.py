from flask import Blueprint, jsonify
from app.models.series import Series

series_bp = Blueprint('series', __name__, url_prefix='/api')

@series_bp.route('/series')
def get_series():
    all_series = Series.query.order_by(Series.created_at.desc()).all()
    return jsonify([s.to_dict() for s in all_series])

@series_bp.route('/series/<slug>')
def get_one_series(slug):
    s = Series.query.filter_by(slug=slug).first_or_404()
    return jsonify(s.to_dict())