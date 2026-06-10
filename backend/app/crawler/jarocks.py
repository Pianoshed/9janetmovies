import os
import re
import time
import logging

import requests
from bs4 import BeautifulSoup

from app import db
from app.models.series import Series
from app.models.episode import Episode
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

JAROCK_BASE     = 'https://9jarocks.net'
JAROCK_STATE    = os.getenv('JAROCK_STATE_FILE', _default_state_file('9jarocks_processed.txt'))
JAROCK_DELAY    = float(os.getenv('JAROCK_DELAY', 1.0))
JAROCK_TIMEOUT  = int(os.getenv('JAROCK_TIMEOUT', 15))
JAROCK_MAX_PAGES = int(os.getenv('JAROCK_MAX_PAGES', 10))  # per category

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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# Matches: Show.Name.S01E02.720p... or Show Name - S01E02...
_EP_RE = re.compile(
    r'(?P<show>.+?)[\s.\-–]+[Ss](?P<season>\d+)[Ee](?P<episode>\d+)',
    re.IGNORECASE,
)

# Matches season pack pages: "Show Name Season 3" with no episode number
_SEASON_PACK_RE = re.compile(r'^(.+?)\s+[Ss]eason\s+(\d+)', re.IGNORECASE)


def _get(url):
    try:
        time.sleep(JAROCK_DELAY)
        r = requests.get(url, headers=HEADERS, timeout=JAROCK_TIMEOUT)
        r.raise_for_status()
        return r
    except Exception as exc:
        log.error(f'GET failed {url!r}: {exc}')
        return None


def _parse_episode_from_filename(filename):
    """Extract show/season/episode from a filename like Show.S01E02.720p.mkv"""
    # Strip extension and junk tags like [9jaRocks.Com]
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


def _crawl_post(post_url, page_title, processed):
    """Scrape a single post page and save all DOWNLOAD links found."""
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
            # Fallback: use page title for show/season, episode=0 (pack)
            label = f'S{fallback_season:02d}E00'
            _save_episode(fallback_show, fallback_season, 0, label, href)

        saved += 1

    _mark_url_processed(JAROCK_STATE, post_url)
    return saved


def _crawl_category(cat_url, processed):
    """Paginate through a category and crawl each post."""
    log.info(f'  Category: {cat_url}')
    total = 0

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
            saved = _crawl_post(post_url, title, processed)
            total += saved

    return total


def run_9jarocks_crawl():
    processed = _load_processed_urls(JAROCK_STATE)
    log.info(f'═══ 9jaRocks crawl | already seen: {len(processed)} ═══')

    total = 0
    for cat_url in SERIES_CATEGORIES:
        total += _crawl_category(cat_url, processed)

    log.info(f'═══ 9jaRocks crawl done: {total} episodes saved ═══')