from flask import Blueprint, jsonify, request
import threading
import os

crawler_bp = Blueprint('crawler', __name__)

CRAWLER_SECRET = os.getenv('CRAWLER_SECRET', 'secret123')

@crawler_bp.route('/api/crawl', methods=['POST'])
def trigger_crawl():
    # Protect the route with a secret key
    token = request.headers.get('X-Crawler-Token')
    if token != CRAWLER_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.dldownload import run_crawl
    from flask import current_app

    app = current_app._get_current_object()

    def run():
        with app.app_context():
            run_crawl(
                max_urls=100,
                include_dldownload=True,
                include_thenkiri=True,
                thenkiri_max=200,
                fetch_thenkiri_pages=False
            )

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'Crawler started in background'}), 200