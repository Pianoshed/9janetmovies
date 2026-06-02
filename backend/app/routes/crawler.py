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

    from app.crawler.dldownload import DLDOWNLOAD_STATE, THENKIRI_STATE, MEETDOWNLOAD_STATE

    for state_file in [DLDOWNLOAD_STATE, THENKIRI_STATE, MEETDOWNLOAD_STATE]:
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
                include_meetdownload=True,
                thenkiri_max=550,
                meetdownload_max=200,
                fetch_thenkiri_pages=False
            )

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'Crawler started in background'}), 200


@crawler_bp.route('/api/crawl/dldownload', methods=['POST'])
def trigger_dldownload_crawl():
    token = request.headers.get('X-Crawler-Token')
    if token != CRAWLER_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.dldownload import run_dldownload_crawl
    from flask import current_app

    app = current_app._get_current_object()

    def run():
        with app.app_context():
            run_dldownload_crawl(max_urls=550)

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'DLDownload crawl started'}), 200


@crawler_bp.route('/api/crawl/thenkiri', methods=['POST'])
def trigger_thenkiri_crawl():
    token = request.headers.get('X-Crawler-Token')
    if token != CRAWLER_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.dldownload import run_thenkiri_crawl
    from flask import current_app

    app = current_app._get_current_object()

    def run():
        with app.app_context():
            run_thenkiri_crawl(max_urls=550, fetch_pages=False)

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'TheNkiri crawl started'}), 200


@crawler_bp.route('/api/crawl/meetdownload', methods=['POST'])
def trigger_meetdownload_crawl():
    token = request.headers.get('X-Crawler-Token')
    if token != CRAWLER_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.dldownload import run_meetdownload_crawl
    from flask import current_app

    app = current_app._get_current_object()

    def run():
        with app.app_context():
            run_meetdownload_crawl(max_urls=200)

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'MeetDownload crawl started'}), 200


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


@crawler_bp.route('/api/crawl/blog', methods=['POST'])
def trigger_blog_crawl():
    token = request.headers.get('X-Crawler-Token')
    if token != CRAWLER_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.blog import run_blog_crawl
    from flask import current_app

    app = current_app._get_current_object()

    def run():
        with app.app_context():
            run_blog_crawl()

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'Blog crawl started'}), 200