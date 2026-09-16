import os
import re
import time
import logging

import requests
from bs4 import BeautifulSoup

from app import db
from app.models.series import Series
from app.models.episode import Episode
from app.models.movie import Movie
from app.models.download_link import DownloadLink
from app.crawler.dldownload import (
    slugify,
    tmdb_search,
    clean_title_for_search,
    detect_genre_from_title,
    is_adult_content,
    _default_state_file,
    _load_processed_urls,
    _mark_url_processed,
)

log = logging.getLogger(__name__)

JAROCK_BASE      = 'https://9jarocks.net'
JAROCK_STATE     = os.getenv('JAROCK_STATE_FILE', _default_state_file('9jarocks_processed.txt'))
JAROCK_DELAY     = float(os.getenv('JAROCK_DELAY', 1.5))
JAROCK_TIMEOUT   = int(os.getenv('JAROCK_TIMEOUT', 20))
JAROCK_MAX_PAGES = int(os.getenv('JAROCK_MAX_PAGES', 10))

# --- new: retry / backoff tuning ---
JAROCK_DIRECT_RETRIES = int(os.getenv('JAROCK_DIRECT_RETRIES', 1))   # attempts before falling back to proxy
JAROCK_PROXY_RETRIES  = int(os.getenv('JAROCK_PROXY_RETRIES', 2))    # attempts against ScrapingDog
JAROCK_PROXY_TIMEOUT  = int(os.getenv('JAROCK_PROXY_TIMEOUT', 60))   # ScrapingDog retries server-side for up to 60s
JAROCK_BACKOFF_BASE   = float(os.getenv('JAROCK_BACKOFF_BASE', 3.0))  # seconds, doubles each retry

SCRAPINGDOG_API_KEY = os.getenv('SCRAPINGDOG_API_KEY', '')
SCRAPINGDOG_DYNAMIC = os.getenv('SCRAPINGDOG_DYNAMIC', 'false')  # 'true' enables JS rendering (costs more credits)
log.info(f"SCRAPINGDOG_API_KEY loaded: {'YES' if SCRAPINGDOG_API_KEY else 'NO'}")

# Series categories only — skip movies
SERIES_CATEGORIES = [
    'https://9jarocks.net/category/videodownload/hollywood-tv-series',
    'https://9jarocks.net/category/videodownload/nollywood-tv-series',
    'https://9jarocks.net/category/videodownload/other-foreign-series',
    'https://9jarocks.net/category/videodownload/korean-drama',
    'https://9jarocks.net/category/videodownload/thai-drama',
    'https://9jarocks.net/category/videodownload/chinese-drama',
    'https://9jarocks.net/category/videodownload/anime',
    'https://9jarocks.net/category/videodownload/ongoing',
]

# Movie categories
MOVIE_CATEGORIES = [
    'https://9jarocks.net/category/videodownload/hollywood-movie',
    'https://9jarocks.net/category/videodownload/foreign-movies',
    'https://9jarocks.net/category/videodownload/nollywood-movie',
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site',
}

# Matches: Show.Name.S01E02.720p... or Show Name - S01E02...
_EP_RE = re.compile(
    r'(?P<show>.+?)[\s.\-–]+[Ss](?P<season>\d+)[Ee](?P<episode>\d+)',
    re.IGNORECASE,
)

# Matches season pack pages: "Show Name Season 3" with no episode number
_SEASON_PACK_RE = re.compile(r'^(.+?)\s+[Ss]eason\s+(\d+)', re.IGNORECASE)

# Matches a 4-digit release year, e.g. "Movie Title (2024)" or "Movie Title 2024 720p"
_YEAR_RE = re.compile(r'(?:19|20)\d{2}')

# Matches a resolution/quality token in a filename, e.g. 720p, 1080p, 480p, 2160p
_QUALITY_RE = re.compile(r'\b(\d{3,4}p)\b', re.IGNORECASE)


def _is_dns_failure(exc):
    """True if this exception is a DNS/NameResolutionError rather than a timeout/connection reset."""
    msg = str(exc)
    return 'NameResolutionError' in msg or 'Failed to resolve' in msg


def _get(url):
    """
    Try direct request first (with a couple of quick retries — worth doing since
    DNS/connection blips are often transient). On repeated failure or a block
    status code, fall back to ScrapingDog with its own retries and a longer
    timeout, since ScrapingDog itself can take a while to come back on tougher
    pages (it retries server-side for up to 60s before giving up).
    """
    time.sleep(JAROCK_DELAY)

    # --- Direct attempts ---
    last_dns_failure = False
    for attempt in range(1, JAROCK_DIRECT_RETRIES + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=JAROCK_TIMEOUT)
            if r.status_code == 200:
                return r
            if r.status_code not in (403, 429, 503):
                r.raise_for_status()
            log.warning(f'Direct request blocked ({r.status_code}) for {url!r} — trying proxy')
            break  # a block status code won't fix itself with a same-path retry
        except requests.exceptions.RequestException as exc:
            last_dns_failure = _is_dns_failure(exc)
            log.warning(
                f'Direct request failed for {url!r} (attempt {attempt}/{JAROCK_DIRECT_RETRIES}): {exc}'
            )
            if attempt < JAROCK_DIRECT_RETRIES:
                time.sleep(JAROCK_BACKOFF_BASE * attempt)

    if last_dns_failure:
        log.warning(f'Direct DNS resolution failing for {url!r} — trying proxy')
    else:
        log.warning(f'Direct request exhausted for {url!r} — trying proxy')

    # --- ScrapingDog fallback, with its own retries ---
    # ScrapingDog isn't a proxy you route requests through — it's a GET endpoint
    # that fetches the target URL server-side and hands back the raw HTML.
    if not SCRAPINGDOG_API_KEY:
        log.error(f'No SCRAPINGDOG_API_KEY set; cannot bypass block for {url!r}')
        return None

    sd_url = 'https://api.scrapingdog.com/scrape'
    sd_params = {
        'api_key': SCRAPINGDOG_API_KEY,
        'url': url,
        'dynamic': SCRAPINGDOG_DYNAMIC,
    }

    for attempt in range(1, JAROCK_PROXY_RETRIES + 1):
        try:
            r = requests.get(sd_url, params=sd_params, timeout=JAROCK_PROXY_TIMEOUT)
            # ScrapingDog returns 410 if it couldn't fetch the page within its own
            # 60s retry window — you aren't charged for that one, safe to retry.
            if r.status_code == 410:
                log.warning(f'ScrapingDog returned 410 (unfetchable) for {url!r} — retrying')
                if attempt < JAROCK_PROXY_RETRIES:
                    time.sleep(JAROCK_BACKOFF_BASE * attempt)
                continue
            r.raise_for_status()
            log.info(f'ScrapingDog succeeded for {url!r} (attempt {attempt}/{JAROCK_PROXY_RETRIES})')
            return r
        except Exception as exc:
            log.error(
                f'ScrapingDog failed for {url!r} (attempt {attempt}/{JAROCK_PROXY_RETRIES}): {exc}'
            )
            if attempt < JAROCK_PROXY_RETRIES:
                time.sleep(JAROCK_BACKOFF_BASE * attempt)

    log.error(f'ScrapingDog exhausted retries for {url!r} — giving up')
    return None


def _parse_episode_from_filename(filename):
    """Extract show/season/episode from a filename like Show.S01E02.720p.mkv"""
    stem = re.sub(r'\.[a-zA-Z0-9]{2,4}$', '', filename)
    stem = re.sub(r'\[.*?\]', '', stem)
    stem = stem.strip()
    m = _EP_RE.search(stem)
    if not m:
        return None
    show = m.group('show').replace('.', ' ').strip()
    show = re.sub(r'\s+', ' ', show)
    return {
        'show':    show,
        'season':  int(m.group('season')),
        'episode': int(m.group('episode')),
        'label':   f'S{int(m.group("season")):02d}E{int(m.group("episode")):02d}',
    }


def _parse_page_title(title):
    """
    Fallback: parse show/season from the post title when filenames aren't enough.
    e.g. 'Wura Season 4 (Episode 47 - 50 Added)' -> show='Wura', season=4
    """
    m = _SEASON_PACK_RE.match(title)
    if m:
        return m.group(1).strip(), int(m.group(2))
    return title.strip(), 1


def _parse_movie_title(title):
    """
    Strip a trailing/embedded year and junk like (2024) or [2024] from a movie
    post title, returning (clean_title, year_or_None). Quality tokens like
    720p/1080p are stripped too, so different-quality posts for the same film
    collapse onto the same slug instead of creating duplicate Movie rows.
    e.g. 'Inception (2010) 1080p' -> ('Inception', 2010)
    """
    year = None
    m = _YEAR_RE.search(title)
    if m:
        year = int(m.group(0))

    clean = title
    clean = re.sub(r'[\(\[]?\s*(?:19|20)\d{2}\s*[\)\]]?', '', clean)
    clean = _QUALITY_RE.sub('', clean)
    clean = re.sub(r'\s+', ' ', clean).strip(' -–([])')
    return clean or title.strip(), year


def _parse_quality_from_filename(filename):
    """Pull a resolution/quality label like '720p' out of a filename, if present."""
    m = _QUALITY_RE.search(filename)
    return m.group(1) if m else None


def _save_episode(show_title, season, episode, label, video_url):
    if is_adult_content(show_title, video_url):
        log.info(f'  Blocked adult content: {show_title!r}')
        return

    series_slug = slugify(show_title)
    if not series_slug or series_slug == 'untitled':
        log.warning(f'  Skipped — bad slug: {show_title!r}')
        return

    search_q = clean_title_for_search(show_title)
    tmdb = tmdb_search(search_q, prefer_tv=True) or tmdb_search(search_q, prefer_tv=False)

    poster      = tmdb.get('poster')      if tmdb else None
    description = tmdb.get('description') if tmdb else ''
    genre       = (tmdb.get('genre') if tmdb else None) or detect_genre_from_title(show_title)

    try:
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(Series).values(
            title       = show_title,
            slug        = series_slug,
            poster_url  = poster,
            genre       = genre,
            description = description,
        ).on_conflict_do_update(
            index_elements=['slug'],
            set_={
                'poster_url': db.case(
                    (Series.poster_url == None, pg_insert(Series).excluded.poster_url),
                    (
                        db.and_(
                            Series.poster_url.notlike('%image.tmdb.org%'),
                            pg_insert(Series).excluded.poster_url.like('%image.tmdb.org%'),
                        ),
                        pg_insert(Series).excluded.poster_url,
                    ),
                    else_=Series.poster_url,
                ),
                'description': db.case(
                    (Series.description == None, pg_insert(Series).excluded.description),
                    (Series.description == '',   pg_insert(Series).excluded.description),
                    else_=Series.description,
                ),
            }
        ).returning(Series.id)

        result    = db.session.execute(stmt)
        db.session.commit()
        series_id = result.fetchone()[0]

        existing = Episode.query.filter_by(
            series_id=series_id, season=season, episode=episode
        ).first()

        if not existing:
            db.session.add(Episode(
                series_id = series_id,
                season    = season,
                episode   = episode,
                title     = f'{show_title} {label}',
                url       = video_url,
                host      = '9jaRocks',
            ))
            db.session.commit()
            log.info(f'  ✓ {show_title} {label} | poster: {"✓" if poster else "✗"}')
        else:
            log.info(f'  Already exists: {show_title} {label}')

    except Exception as exc:
        db.session.rollback()
        log.error(f'  DB error for "{show_title} {label}": {exc}')


def _save_movie(movie_title, year, label, video_url):
    """Upsert a Movie by slug, then add a DownloadLink for it if not already present."""
    if is_adult_content(movie_title, video_url):
        log.info(f'  Blocked adult content: {movie_title!r}')
        return

    movie_slug = slugify(movie_title)
    if not movie_slug or movie_slug == 'untitled':
        log.warning(f'  Skipped — bad slug: {movie_title!r}')
        return

    search_q = clean_title_for_search(movie_title)
    tmdb = tmdb_search(search_q, prefer_tv=False)

    poster      = tmdb.get('poster')      if tmdb else None
    description = tmdb.get('description') if tmdb else ''
    genre       = (tmdb.get('genre') if tmdb else None) or detect_genre_from_title(movie_title)
    tmdb_year   = tmdb.get('year') if tmdb else None

    try:
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(Movie).values(
            title       = movie_title,
            slug        = movie_slug,
            poster_url  = poster,
            year        = year or tmdb_year,
            genre       = genre,
            description = description,
        ).on_conflict_do_update(
            index_elements=['slug'],
            set_={
                'poster_url': db.case(
                    (Movie.poster_url == None, pg_insert(Movie).excluded.poster_url),
                    (
                        db.and_(
                            Movie.poster_url.notlike('%image.tmdb.org%'),
                            pg_insert(Movie).excluded.poster_url.like('%image.tmdb.org%'),
                        ),
                        pg_insert(Movie).excluded.poster_url,
                    ),
                    else_=Movie.poster_url,
                ),
                'description': db.case(
                    (Movie.description == None, pg_insert(Movie).excluded.description),
                    (Movie.description == '',   pg_insert(Movie).excluded.description),
                    else_=Movie.description,
                ),
                'year': db.case(
                    (Movie.year == None, pg_insert(Movie).excluded.year),
                    else_=Movie.year,
                ),
            }
        ).returning(Movie.id)

        result   = db.session.execute(stmt)
        db.session.commit()
        movie_id = result.fetchone()[0]

        existing = DownloadLink.query.filter_by(
            movie_id=movie_id, url=video_url
        ).first()

        if not existing:
            db.session.add(DownloadLink(
                movie_id = movie_id,
                label    = label,
                url      = video_url,
                host     = '9jaRocks',
            ))
            db.session.commit()
            log.info(f'  ✓ {movie_title} ({year or "?"}) [{label}] | poster: {"✓" if poster else "✗"}')
        else:
            log.info(f'  Already exists: {movie_title} [{label}]')

    except Exception as exc:
        db.session.rollback()
        log.error(f'  DB error for movie "{movie_title}": {exc}')


def _crawl_post(post_url, page_title, processed):
    """Scrape a single series post page and save all DOWNLOAD links found."""
    if post_url in processed:
        return 0

    r = _get(post_url)
    if not r:
        return 0

    soup = BeautifulSoup(r.text, 'html.parser')
    fallback_show, fallback_season = _parse_page_title(page_title)
    saved = 0

    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.text.strip().upper()

        # Only follow direct download links
        if text != 'DOWNLOAD' and 'loadedfiles.org' not in href:
            continue
        if not href.startswith('http'):
            continue

        # Try to parse episode info from the URL filename
        filename = href.rstrip('/').split('/')[-1]
        parsed = _parse_episode_from_filename(filename)

        if parsed:
            _save_episode(parsed['show'], parsed['season'], parsed['episode'], parsed['label'], href)
        else:
            label = f'S{fallback_season:02d}E00'
            _save_episode(fallback_show, fallback_season, 0, label, href)

        saved += 1

    _mark_url_processed(JAROCK_STATE, post_url)
    return saved


def _crawl_movie_post(post_url, page_title, processed):
    """Scrape a single movie post page and save all DOWNLOAD links found as DownloadLinks."""
    if post_url in processed:
        return 0

    r = _get(post_url)
    if not r:
        return 0

    soup = BeautifulSoup(r.text, 'html.parser')
    fallback_title, fallback_year = _parse_movie_title(page_title)
    saved = 0

    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.text.strip().upper()

        # Only follow direct download links
        if text != 'DOWNLOAD' and 'loadedfiles.org' not in href:
            continue
        if not href.startswith('http'):
            continue

        filename = href.rstrip('/').split('/')[-1]
        quality  = _parse_quality_from_filename(filename) or 'Download'

        _save_movie(fallback_title, fallback_year, quality, href)
        saved += 1

    _mark_url_processed(JAROCK_STATE, post_url)
    return saved

def _find_movie_post_url(title):
    """Search 9jarocks (WordPress ?s= search) for a title, return matching post links."""
    from urllib.parse import quote_plus
    search_url = f'{JAROCK_BASE}/?s={quote_plus(title)}'
    r = _get(search_url)
    if not r:
        return []

    soup = BeautifulSoup(r.text, 'html.parser')
    posts, seen = [], set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/videodownload/' in href and re.search(r'-id\d+\.html$', href) and href not in seen:
            seen.add(href)
            posts.append((href, a.text.strip()))
    return posts


def crawl_single_movie(title=None, post_url=None, force=True):
    """
    Backfill one movie: pass a title to search 9jarocks for its post,
    or a post_url directly if you already have it.
    force=True bypasses the JAROCK_STATE file so an already-attempted
    (but empty/failed) post gets re-scraped.
    """
    processed = set() if force else _load_processed_urls(JAROCK_STATE)

    if post_url:
        candidates = [(post_url, title or '')]
    else:
        if not title:
            log.error('crawl_single_movie needs a title or post_url')
            return 0
        candidates = _find_movie_post_url(title)
        if not candidates:
            log.warning(f'No 9jaRocks post found for {title!r}')
            return 0

    total = 0
    for href, listing_title in candidates:
        r = _get(href)
        page_title = listing_title
        if r:
            soup = BeautifulSoup(r.text, 'html.parser')
            og = soup.find('meta', property='og:title')
            if og and og.get('content'):
                page_title = og['content']
            elif soup.title:
                page_title = soup.title.text.strip()

        saved = _crawl_movie_post(href, page_title, processed)
        total += saved
        log.info(f'  {href} -> {saved} link(s) saved')

    return total

def _crawl_category(cat_url, processed, is_movie=False):
    """Paginate through a category and crawl each post (series or movie)."""
    log.info(f'  Category: {cat_url}')
    total = 0
    crawl_post_fn = _crawl_movie_post if is_movie else _crawl_post

    for page in range(1, JAROCK_MAX_PAGES + 1):
        url = cat_url if page == 1 else f'{cat_url}/page/{page}/'
        r = _get(url)
        if not r:
            break

        soup = BeautifulSoup(r.text, 'html.parser')

        # Collect post links — 9jarocks post URLs follow /videodownload/...-idNNNNNN.html
        post_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/videodownload/' in href and re.search(r'-id\d+\.html$', href):
                title = a.text.strip() or ''
                post_links.append((href, title))

        # Deduplicate while preserving order
        seen = set()
        unique_posts = []
        for href, title in post_links:
            if href not in seen:
                seen.add(href)
                unique_posts.append((href, title))

        if not unique_posts:
            log.info(f'    Page {page}: no posts found — stopping pagination')
            break

        log.info(f'    Page {page}: {len(unique_posts)} posts')
        for post_url, title in unique_posts:
            saved = crawl_post_fn(post_url, title, processed)
            total += saved

    return total


def run_9jarocks_crawl():
    processed = _load_processed_urls(JAROCK_STATE)
    log.info(f'═══ 9jaRocks crawl | already seen: {len(processed)} ═══')

    total = 0
    for cat_url in SERIES_CATEGORIES:
        total += _crawl_category(cat_url, processed, is_movie=False)

    for cat_url in MOVIE_CATEGORIES:
        total += _crawl_category(cat_url, processed, is_movie=True)

    log.info(f'═══ 9jaRocks crawl done: {total} items saved ═══')