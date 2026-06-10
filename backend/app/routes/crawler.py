from flask import Blueprint, jsonify, request, current_app
import threading
import os

crawler_bp = Blueprint('crawler', __name__)

CRAWLER_SECRET = os.getenv('CRAWLER_SECRET', 'secret123')


def _auth(req):
    return req.headers.get('X-Crawler-Token') == CRAWLER_SECRET


def _thread(app, fn, *args, **kwargs):
    def run():
        with app.app_context():
            fn(*args, **kwargs)
    t = threading.Thread(target=run, daemon=True)
    t.start()


@crawler_bp.route('/api/crawl/reset', methods=['POST'])
def reset_crawl_state():
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.dldownload import DLDOWNLOAD_STATE, THENKIRI_STATE, LOADEDFILES_STATE
    from app.crawler.o2tv_crawler import O2TV_STATE

    for state_file in [DLDOWNLOAD_STATE, THENKIRI_STATE, LOADEDFILES_STATE, O2TV_STATE]:
        try:
            open(state_file, 'w').close()
        except Exception:
            pass

    return jsonify({'status': 'State reset — next crawl will process all URLs'}), 200


@crawler_bp.route('/api/crawl', methods=['POST'])
def trigger_crawl():
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.dldownload import run_crawl

    _thread(current_app._get_current_object(), run_crawl,
        max_urls=550,
        include_dldownload=True,
        include_thenkiri=True,
        include_loadedfiles=True,
        thenkiri_max=550,
        loadedfiles_max=550,
        fetch_thenkiri_pages=False,
        fetch_loadedfiles_pages=False,
    )
    return jsonify({'status': 'Crawler started in background'}), 200


@crawler_bp.route('/api/crawl/dldownload', methods=['POST'])
def trigger_dldownload_crawl():
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.dldownload import run_dldownload_crawl

    _thread(current_app._get_current_object(), run_dldownload_crawl, max_urls=550)
    return jsonify({'status': 'DLDownload crawl started'}), 200


@crawler_bp.route('/api/crawl/thenkiri', methods=['POST'])
def trigger_thenkiri_crawl():
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.dldownload import run_thenkiri_crawl

    _thread(current_app._get_current_object(), run_thenkiri_crawl, max_urls=600, fetch_pages=False)
    return jsonify({'status': 'TheNkiri crawl started'}), 200


@crawler_bp.route('/api/crawl/loadedfiles', methods=['POST'])
def trigger_loadedfiles_crawl():
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.dldownload import run_loadedfiles_crawl

    _thread(current_app._get_current_object(), run_loadedfiles_crawl, max_urls=550, fetch_pages=False)
    return jsonify({'status': 'LoadedFiles crawl started'}), 200


@crawler_bp.route('/api/crawl/youtube', methods=['POST'])
def trigger_youtube_crawl():
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.youtube import run_youtube_crawl

    _thread(current_app._get_current_object(), run_youtube_crawl, max_results_per_query=20)
    return jsonify({'status': 'YouTube crawl started'}), 200


@crawler_bp.route('/api/crawl/o2tv', methods=['POST'])
def trigger_o2tv_crawl():
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.o2tv_crawler import run_o2tv_crawl

    base_url = request.json.get('base_url') if request.is_json else None
    _thread(current_app._get_current_object(), run_o2tv_crawl, base_url=base_url)
    return jsonify({'status': 'O2TV crawl started'}), 200


@crawler_bp.route('/api/crawl/blog', methods=['POST'])
def trigger_blog_crawl():
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.blog import run_blog_crawl

    _thread(current_app._get_current_object(), run_blog_crawl)
    return jsonify({'status': 'Blog crawl started'}), 200


@crawler_bp.route('/api/crawl/backfill', methods=['POST'])
def trigger_backfill():
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    from app.crawler.dldownload import backfill_descriptions

    _thread(current_app._get_current_object(), backfill_descriptions, batch_size=500)
    return jsonify({'status': 'Backfill started — filling empty descriptions from TMDB'}), 200