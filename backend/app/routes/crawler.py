from flask import Blueprint, jsonify, request
import threading
import os

crawler_bp = Blueprint('crawler', __name__)

CRAWLER_SECRET = os.getenv('CRAWLER_SECRET', 'secret123')


@crawler_bp.route('/api/crawl/reset', methods=['POST'])
def reset_crawl_state():
    token = request.headers.get('X-Crawler-Token')
    if token != CRAWLER_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.dldownload import DLDOWNLOAD_STATE, THENKIRI_STATE

    for state_file in [DLDOWNLOAD_STATE, THENKIRI_STATE]:
        try:
            open(state_file, 'w').close()
        except Exception:
            pass

    return jsonify({'status': 'State reset — next crawl will process all URLs'}), 200


@crawler_bp.route('/api/crawl', methods=['POST'])
def trigger_crawl():
    token = request.headers.get('X-Crawler-Token')
    if token != CRAWLER_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.dldownload import run_crawl
    from flask import current_app

    app = current_app._get_current_object()

    def run():
        with app.app_context():
            run_crawl(
                max_urls=550,
                include_dldownload=True,
                include_thenkiri=True,
                thenkiri_max=550,
                fetch_thenkiri_pages=False
            )

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'Crawler started in background'}), 200


@crawler_bp.route('/api/crawl/youtube', methods=['POST'])
def trigger_youtube_crawl():
    token = request.headers.get('X-Crawler-Token')
    if token != CRAWLER_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.youtube import run_youtube_crawl
    from flask import current_app

    app = current_app._get_current_object()

    def run():
        with app.app_context():
            run_youtube_crawl(max_results_per_query=20)

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'YouTube crawl started'}), 200