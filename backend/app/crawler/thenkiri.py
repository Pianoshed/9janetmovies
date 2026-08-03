import re
import time
import logging

from bs4 import BeautifulSoup

from app.crawler.dldownload import (
    # shared HTTP / parsing helpers
    _safe_get,
    _load_processed_urls,
    _mark_url_processed,
    _default_state_file,
    _best_poster,
    _is_valid_poster,
    # title / classification helpers
    slugify,
    clean_movie_title,
    clean_series_title,
    is_series,
    is_series_from_url,
    is_adult_content,
    detect_genre_from_url,
    detect_genre_from_title,
    detect_year_from_text,
    # TMDB + persistence
    tmdb_search,
    save_movie,
    save_series,
    CURRENT_YEAR,
)

import os

log = logging.getLogger(__name__)

THENKIRI_BASE = 'https://thenkiri.com'

THENKIRI_SITEMAPS = [
    'https://thenkiri.com/post-sitemap.xml',
    'https://thenkiri.com/post-sitemap2.xml',
    'https://thenkiri.com/post-sitemap3.xml',
    'https://thenkiri.com/post-sitemap4.xml',
    'https://thenkiri.com/post-sitemap5.xml',
    'https://thenkiri.com/post-sitemap6.xml',
    'https://thenkiri.com/post-sitemap7.xml',
]

THENKIRI_STATE = os.getenv('THENKIRI_STATE_FILE', _default_state_file('thenkiri_processed.txt'))

SLEEP_THENKIRI_LOOP = float(os.getenv('SLEEP_THENKIRI_LOOP', 0.3))
SLEEP_THENKIRI_PAGE = float(os.getenv('SLEEP_THENKIRI_PAGE', 0.5))
SLEEP_SITEMAP       = float(os.getenv('SLEEP_SITEMAP', 0.5))

SKIP_URL_SEGMENTS = ('/page/', '/category/', '/tag/', '/author/')

IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.webp')


# ─────────────────────────────────────────────────────────────────────────
# Sitemap parsing
# ─────────────────────────────────────────────────────────────────────────

def _extract_poster_from_url_tag(url_tag, page_url):
    """Pull a thumbnail out of a sitemap <url> block, if present."""
    for img_tag in url_tag.find_all('image:loc'):
        img_url = img_tag.text.strip()
        if (
            img_url != page_url
            and 'use-on-site' not in img_url
            and img_url.startswith('http')
            and img_url.lower().endswith(IMAGE_EXTS)
        ):
            return img_url

    locs = url_tag.find_all('loc')
    for loc in locs[1:]:
        img_url = loc.text.strip()
        if (
            img_url != page_url
            and 'use-on-site' not in img_url
            and img_url.startswith('http')
            and img_url.lower().endswith(IMAGE_EXTS)
        ):
            return img_url

    raw = str(url_tag)
    m = re.search(
        r'<image:loc>(https?://[^<]+\.(?:jpg|jpeg|png|webp))</image:loc>',
        raw, re.IGNORECASE
    )
    if m and 'use-on-site' not in m.group(1):
        return m.group(1)

    return None


def get_thenkiri_entries(max_urls=500, sitemaps=None):
    """Walk the thenkiri sitemaps and return [{title, url, poster}, ...]."""
    if sitemaps is None:
        sitemaps = list(reversed(THENKIRI_SITEMAPS))

    entries, seen_urls = [], set()

    for sitemap_url in sitemaps:
        if len(entries) >= max_urls:
            break

        res = _safe_get(sitemap_url, timeout=15)
        if not res:
            log.error(f'Could not fetch thenkiri sitemap: {sitemap_url}')
            time.sleep(SLEEP_SITEMAP)
            continue

        try:
            soup = BeautifulSoup(res.text, 'xml')
            url_tags = soup.find_all('url')
            log.info(f'  {sitemap_url}: {len(url_tags)} <url> tags found')

            for url_tag in reversed(url_tags):
                if len(entries) >= max_urls:
                    break

                loc = url_tag.find('loc')
                if not loc:
                    continue

                page_url = loc.text.strip()
                if page_url in seen_urls:
                    continue
                seen_urls.add(page_url)

                if any(seg in page_url for seg in SKIP_URL_SEGMENTS):
                    continue
                if is_adult_content('', page_url):
                    continue

                poster = _extract_poster_from_url_tag(url_tag, page_url)
                if poster and not _is_valid_poster(poster):
                    poster = None

                slug_part = page_url.rstrip('/').split('/')[-1]
                raw_title = slug_part.replace('-', ' ').title()

                if is_adult_content(raw_title, page_url):
                    continue

                entries.append({'title': raw_title, 'url': page_url, 'poster': poster})

        except Exception as exc:
            log.error(f'thenkiri sitemap parse error ({sitemap_url}): {exc}')

        log.info(f'  Got {len(entries)} thenkiri entries so far')
        time.sleep(SLEEP_SITEMAP)

    log.info(f'Total thenkiri entries fetched: {len(entries)}')
    return entries


# ─────────────────────────────────────────────────────────────────────────
# Single-page scrape
# ─────────────────────────────────────────────────────────────────────────

def scrape_thenkiri_page(url):
    """Fetch one thenkiri post and pull title/description/poster from it."""
    res = _safe_get(url)
    if not res:
        return None

    try:
        soup = BeautifulSoup(res.text, 'lxml')

        title = None
        for sel in ['h1.entry-title', 'h1', '.entry-title']:
            tag = soup.select_one(sel)
            if tag:
                title = tag.get_text(strip=True)
                break

        if not title and soup.title:
            title = soup.title.text.strip()
            title = re.sub(r'\s*[|\-–]\s*.*?(thenkiri).*$', '', title, flags=re.IGNORECASE)

        if title and is_adult_content(title, url):
            return None

        description = ''
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content', '')[:500]

        poster = None
        for attr in [{'property': 'og:image'}, {'name': 'twitter:image'}]:
            tag = soup.find('meta', attr)
            if tag:
                img = tag.get('content', '').strip()
                if img.startswith('http') and 'use-on-site' not in img:
                    poster = img
                    break

        return {
            'title':       title.strip() if title else None,
            'description': description,
            'poster':      poster,
        }

    except Exception as exc:
        log.error(f'thenkiri page scrape error {url}: {exc}')
        return None


# ─────────────────────────────────────────────────────────────────────────
# One entry -> DB (shared by full crawl and single-entry backfill)
# ─────────────────────────────────────────────────────────────────────────

def _process_entry(url, sitemap_title=None, sitemap_poster=None, fetch_page=True):
    """
    Turn one thenkiri URL into a saved Movie/Series row.
    sitemap_title/sitemap_poster are the sitemap-derived fallbacks (used when
    fetch_page=False, or when the page fetch itself gets blocked).
    Returns 'movie', 'series', or None (skipped).
    """
    title  = sitemap_title
    poster = sitemap_poster
    description = ''

    if fetch_page:
        page_data = scrape_thenkiri_page(url)
        if page_data is None:
            log.warning(f'  Page fetch blocked/failed — using sitemap data instead: {url}')
        else:
            if page_data.get('title'):
                title = clean_movie_title(page_data['title'])
            if page_data.get('poster'):
                poster = page_data['poster']
            description = page_data.get('description', '')

    if not title:
        log.warning(f'  No usable title for {url} — skipping')
        return None

    if is_adult_content(title, url):
        log.info(f'  Blocked adult content: {title!r}')
        return None

    title_is_series = is_series(title) or is_series_from_url(url)
    search_title = clean_series_title(title) if title_is_series else clean_movie_title(title)

    if not search_title:
        log.info(f'  Skipped — empty title after cleaning: {url}')
        return None

    year = detect_year_from_text(title, url)
    tmdb = tmdb_search(search_title, year=year, prefer_tv=title_is_series)

    best_poster = _best_poster(tmdb.get('poster') if tmdb else None, poster)

    if tmdb:
        if not tmdb.get('poster') and best_poster:
            tmdb['poster'] = best_poster
    else:
        tmdb = {
            'poster':      best_poster,
            'description': description,
            'genre':       detect_genre_from_url(url) or detect_genre_from_title(title),
            'year':        year or CURRENT_YEAR,
        }

    data = {'title': search_title, 'url': url, 'poster': best_poster, 'links': []}

    if title_is_series:
        save_series(data, tmdb, source='thenkiri')
        return 'series'
    else:
        save_movie(data, tmdb, source='thenkiri')
        return 'movie'


# ─────────────────────────────────────────────────────────────────────────
# Full-site crawl
# ─────────────────────────────────────────────────────────────────────────

def run_thenkiri_crawl(max_urls=200, fetch_pages=True):
    log.info('═══ thenkiri crawl ═══')
    total_movies, total_series, total_skipped, total_adult_blocked = 0, 0, 0, 0

    processed = _load_processed_urls(THENKIRI_STATE)
    log.info(f'Already processed: {len(processed)} URLs')

    entries = get_thenkiri_entries(max_urls=max_urls)
    if not entries:
        log.error('No entries from thenkiri sitemaps.')
        return

    entries = [e for e in entries if e['url'] not in processed]
    log.info(f'Processing {len(entries)} new thenkiri entries...')

    for i, entry in enumerate(entries, 1):
        log.info(f'[{i}/{len(entries)}] {entry["url"]}')

        result = _process_entry(
            entry['url'],
            sitemap_title=entry['title'],
            sitemap_poster=entry['poster'],
            fetch_page=fetch_pages,
        )

        if result == 'movie':
            total_movies += 1
        elif result == 'series':
            total_series += 1
        else:
            total_skipped += 1

        _mark_url_processed(THENKIRI_STATE, entry['url'])
        time.sleep(SLEEP_THENKIRI_LOOP if fetch_pages is False else SLEEP_THENKIRI_PAGE)

    log.info(
        f'thenkiri done: {total_movies} movies | {total_series} series | '
        f'{total_skipped} skipped/adult-blocked'
    )


# ─────────────────────────────────────────────────────────────────────────
# Single-entry backfill (the "just this one page" path)
# ─────────────────────────────────────────────────────────────────────────

def _find_thenkiri_url(title):
    """Scan the thenkiri sitemaps for a URL whose slug matches the given title."""
    target_slug = slugify(title)
    matches = []

    for sm_url in THENKIRI_SITEMAPS:
        res = _safe_get(sm_url, timeout=15)
        if not res:
            continue
        soup = BeautifulSoup(res.text, 'xml')
        for loc in soup.find_all('loc'):
            page_url = loc.text.strip()
            if any(seg in page_url for seg in SKIP_URL_SEGMENTS):
                continue
            slug_part = page_url.rstrip('/').split('/')[-1]
            url_slug = slugify(slug_part.replace('-', ' '))
            if target_slug in url_slug or url_slug in target_slug:
                matches.append(page_url)
        time.sleep(SLEEP_SITEMAP)

    return matches


def crawl_single_movie_thenkiri(title=None, post_url=None, force=True):
    """
    Backfill a single thenkiri page.
    Pass post_url directly if you already have it (preferred — skips the sitemap
    scan entirely). Otherwise pass a title and it'll search the sitemaps for a
    matching slug.
    force=True bypasses THENKIRI_STATE so an already-attempted (empty) page
    gets re-scraped.
    """
    processed = set() if force else _load_processed_urls(THENKIRI_STATE)

    if post_url:
        candidates = [post_url]
    else:
        if not title:
            log.error('crawl_single_movie_thenkiri needs a title or post_url')
            return 0
        candidates = _find_thenkiri_url(title)
        if not candidates:
            log.warning(f'No thenkiri sitemap entry matched {title!r}')
            return 0

    total = 0
    for url in candidates:
        if url in processed:
            log.info(f'  Already processed, skipping: {url}')
            continue

        result = _process_entry(url, fetch_page=True)
        _mark_url_processed(THENKIRI_STATE, url)

        if result:
            total += 1
            log.info(f'  ✓ Backfilled ({result}): {url}')
        else:
            log.warning(f'  Nothing saved for: {url}')

    return total