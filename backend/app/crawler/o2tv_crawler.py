import os
import re
import time
import logging
from urllib.parse import urljoin, unquote

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
    CURRENT_YEAR,
)

log = logging.getLogger(__name__)

O2TV_BASE_URL = os.getenv('O2TV_BASE_URL', 'http://d6.o2tv.org/')
O2TV_STATE    = os.getenv('O2TV_STATE_FILE', _default_state_file('o2tv_processed.txt'))
O2TV_DELAY    = float(os.getenv('O2TV_DELAY', 0.5))
O2TV_TIMEOUT  = int(os.getenv('O2TV_TIMEOUT', 15))
O2TV_PROXY    = os.getenv('O2TV_PROXY', None)

VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.wmv', '.flv'}

_EP_RE     = re.compile(r'(?P<show>.+?)\s*[-–]\s*[Ss](?P<season>\d+)[Ee](?P<episode>\d+)', re.IGNORECASE)
_SEASON_RE = re.compile(r'[Ss]eason\s*(\d+)', re.IGNORECASE)

O2TV_HEADERS = {
    'User-Agent':                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept':                    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language':           'en-US,en;q=0.5',
    'Accept-Encoding':           'gzip, deflate',
    'Referer':                   'https://www.google.com/',
    'DNT':                       '1',
    'Connection':                'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


def _get(url):
    try:
        time.sleep(O2TV_DELAY)
        proxies = {'http': O2TV_PROXY, 'https': O2TV_PROXY} if O2TV_PROXY else None
        r = requests.get(url, headers=O2TV_HEADERS, timeout=O2TV_TIMEOUT, proxies=proxies)
        if r.status_code == 403:
            log.error(f'403 Forbidden: {url!r} — server blocked this IP. Set O2TV_PROXY env var to bypass.')
            return None
        r.raise_for_status()
        return r
    except Exception as exc:
        log.error(f'GET failed {url!r}: {exc}')
        return None


def _list_dir(url):
    r = _get(url)
    if not r:
        return []
    soup    = BeautifulSoup(r.text, 'html.parser')
    results = []
    skip    = {'/', '../', '?C=N;O=D', '?C=M;O=A', '?C=S;O=A', '?C=D;O=A'}
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href in skip or href.startswith('?') or (href.startswith('/') and href != '/'):
            continue
        name   = unquote(href.rstrip('/'))
        is_dir = href.endswith('/')
        full   = urljoin(url, href)
        results.append({'name': name, 'href': full, 'is_dir': is_dir})
    return results


def _is_video(name):
    return any(name.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)


def _parse_filename(filename):
    stem = re.sub(r'\.[a-zA-Z0-9]{2,4}$', '', filename)
    stem = re.sub(r'\([^)]*\)', '', stem)
    stem = re.sub(r'\s+[a-z]+-[a-z0-9]+$', '', stem, flags=re.IGNORECASE)
    stem = stem.strip()
    m    = _EP_RE.match(stem)
    if not m:
        return None
    return {
        'show':    m.group('show').strip(),
        'season':  int(m.group('season')),
        'episode': int(m.group('episode')),
        'label':   f'S{int(m.group("season")):02d}E{int(m.group("episode")):02d}',
    }


def _parse_season_num(folder_name):
    m = _SEASON_RE.search(folder_name)
    return int(m.group(1)) if m else 1


def _save_episode(show_title, season, episode, label, video_url):
    if is_adult_content(show_title, video_url):
        log.info(f'  Blocked adult content: {show_title!r}')
        return

    series_slug = slugify(show_title)
    if not series_slug or series_slug == 'untitled':
        log.warning(f'  Skipped — bad slug for: {show_title!r}')
        return

    search_q = clean_title_for_search(show_title)
    tmdb     = tmdb_search(search_q, prefer_tv=True)
    if not tmdb:
        tmdb = tmdb_search(search_q, prefer_tv=False)

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
                            pg_insert(Series).excluded.poster_url.like('%image.tmdb.org%')
                        ),
                        pg_insert(Series).excluded.poster_url
                    ),
                    else_=Series.poster_url
                ),
                'description': db.case(
                    (Series.description == None, pg_insert(Series).excluded.description),
                    (Series.description == '',   pg_insert(Series).excluded.description),
                    else_=Series.description
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
            is_full = (episode == 0)
            db.session.add(Episode(
                series_id = series_id,
                season    = season,
                episode   = episode,
                title     = f'{show_title} {label}',
                url       = video_url,
                host      = 'O2TV',
            ))
            db.session.commit()
            tag = 'Season pack' if is_full else f'S{season:02d}E{episode:02d}'
            log.info(f'  ✓ {tag} → {show_title} | poster: {"✓" if poster else "✗"}')
        else:
            log.info(f'  Already exists: {show_title} {label}')

    except Exception as exc:
        db.session.rollback()
        log.error(f'  DB error for "{show_title} {label}": {exc}')


def _crawl_season(show_title, season_num, season_url, processed):
    log.info(f'    Season {season_num:02d}: {season_url}')
    for entry in _list_dir(season_url):
        name = entry['name']
        href = entry['href']
        if entry['is_dir'] or not _is_video(name) or href in processed:
            continue
        parsed = _parse_filename(name)
        if parsed:
            _save_episode(parsed['show'] or show_title, parsed['season'], parsed['episode'], parsed['label'], href)
        else:
            log.warning(f'    Unrecognised filename: {name!r}')
            _save_episode(show_title, season_num, 0, f'S{season_num:02d}E??', href)
        _mark_url_processed(O2TV_STATE, href)


def _crawl_show(show_name, show_url, processed):
    if is_adult_content(show_name, show_url):
        log.info(f'  Blocked adult show: {show_name!r}')
        return
    log.info(f'  Show: {show_name!r}')
    for entry in _list_dir(show_url):
        name = entry['name']
        href = entry['href']
        if entry['is_dir']:
            _crawl_season(show_name, _parse_season_num(name), href, processed)
        elif _is_video(name) and href not in processed:
            parsed = _parse_filename(name)
            if parsed:
                _save_episode(parsed['show'] or show_name, parsed['season'], parsed['episode'], parsed['label'], href)
            _mark_url_processed(O2TV_STATE, href)


def run_o2tv_crawl(base_url=None):
    base_url  = base_url or O2TV_BASE_URL
    processed = _load_processed_urls(O2TV_STATE)
    log.info(f'═══ O2TV crawl | base: {base_url} | proxy: {"✓" if O2TV_PROXY else "✗"} | already seen: {len(processed)} ═══')

    top = _list_dir(base_url)
    if not top:
        log.error('No entries at O2TV base URL — aborting. If 403, set O2TV_PROXY env var.')
        return

    total = 0
    for entry in top:
        name = entry['name']
        href = entry['href']
        if entry['is_dir']:
            _crawl_show(name, href, processed)
            total += 1
        elif _is_video(name) and href not in processed:
            parsed = _parse_filename(name)
            if parsed:
                _save_episode(parsed['show'], parsed['season'], parsed['episode'], parsed['label'], href)
                _mark_url_processed(O2TV_STATE, href)
                total += 1

    log.info(f'═══ O2TV crawl done: {total} top-level items ═══')