import sys
import argparse
import logging

# ── LOGGING ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

sys.path.insert(0, '.')

from app import create_app
from app.crawler.dldownload import run_crawl

# ── CLI ARGS ──────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description='9janetmovies crawler — scrapes dldownload and thenkiri into the DB.'
)
parser.add_argument(
    '--max-urls',
    type=int,
    default=500,
    help='Max URLs to crawl from dldownload (default: 500)'
)
parser.add_argument(
    '--no-thenkiri',
    action='store_true',
    help='Skip the thenkiri crawl entirely'
)
parser.add_argument(
    '--thenkiri-max',
    type=int,
    default=550,
    help='Max entries to crawl from thenkiri sitemaps (default: 550)'
)
parser.add_argument(
    '--fetch-pages',
    action='store_true',
    help='Fetch each thenkiri page for better titles (slower, ~1s/page)'
)
parser.add_argument(
    '--dldownload-only',
    action='store_true',
    help='Shorthand for --no-thenkiri'
)
parser.add_argument(
    '--thenkiri-only',
    action='store_true',
    help='Skip dldownload and only crawl thenkiri'
)

args = parser.parse_args()

# Resolve source flags
include_dldownload = not args.thenkiri_only
include_thenkiri   = not (args.no_thenkiri or args.dldownload_only)

if not include_dldownload and not include_thenkiri:
    logging.error('Nothing to crawl — --dldownload-only and --thenkiri-only are mutually exclusive.')
    sys.exit(1)

# ── RUN ───────────────────────────────────────────────────────
app = create_app()

with app.app_context():
    run_crawl(
        max_urls             = args.max_urls,
        include_thenkiri     = include_thenkiri,
        include_dldownload   = include_dldownload,
        thenkiri_max         = args.thenkiri_max,
        fetch_thenkiri_pages = args.fetch_pages,
    )