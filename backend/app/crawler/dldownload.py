import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from app import db
from app.models.movie import Movie
from app.models.series import Series
from app.models.episode import Episode
from app.models.download_link import DownloadLink
from sqlalchemy.dialects.postgresql import insert as pg_insert
import re
import time
import logging
import os
import unicodedata
import tempfile
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

CURRENT_YEAR = datetime.now().year

DLDOWNLOAD_BASE  = 'https://dldownload.com.ng'
THENKIRI_BASE    = 'https://thenkiri.com'
LOADEDFILES_BASE = 'https://loadedfiles.org'

THENKIRI_SITEMAPS = [
    'https://thenkiri.com/post-sitemap.xml',
    'https://thenkiri.com/post-sitemap2.xml',
    'https://thenkiri.com/post-sitemap3.xml',
    'https://thenkiri.com/post-sitemap4.xml',
    'https://thenkiri.com/post-sitemap5.xml',
    'https://thenkiri.com/post-sitemap6.xml',
    'https://thenkiri.com/post-sitemap7.xml',
]

LOADEDFILES_SITEMAPS = [
    'https://loadedfiles.org/post-sitemap.xml',
    'https://loadedfiles.org/post-sitemap2.xml',
    'https://loadedfiles.org/post-sitemap3.xml',
    'https://loadedfiles.org/post-sitemap4.xml',
    'https://loadedfiles.org/post-sitemap5.xml',
]

TMDB_KEY  = os.getenv('TMDB_API_KEY')
TMDB_BASE = 'https://api.themoviedb.org/3'
TMDB_IMG  = 'https://image.tmdb.org/t/p/w500'

SLEEP_DLDOWNLOAD      = float(os.getenv('SLEEP_DLDOWNLOAD', 0.8))
SLEEP_THENKIRI_LOOP   = float(os.getenv('SLEEP_THENKIRI_LOOP', 0.3))
SLEEP_THENKIRI_PAGE   = float(os.getenv('SLEEP_THENKIRI_PAGE', 0.5))
SLEEP_LOADEDFILES_LOOP = float(os.getenv('SLEEP_LOADEDFILES_LOOP', 0.4))
SLEEP_LOADEDFILES_PAGE = float(os.getenv('SLEEP_LOADEDFILES_PAGE', 0.6))
SLEEP_SITEMAP         = float(os.getenv('SLEEP_SITEMAP', 0.5))

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}

ADULT_KEYWORDS = [
    'xxx', 'porn', 'pornography', 'adult', 'erotic', 'erotica',
    'sex tape', 'nude', 'naked', 'hardcore', 'softcore', 'fetish',
    'onlyfans', 'brazzers', 'bangbros', 'playboy', 'penthouse',
    'creeping on mom', 'next room affair', 'mamasan',
    'milf', 'stepmom', 'stepsis', 'step-mom', 'step-sis',
    '-18', '+18', '18+', 'x-rated', 'naughty',
]

ADULT_URL_KEYWORDS = [
    '/xxx', 'xxx-', '-xxx', 'adult-', '-adult',
    '/porn', '/erotic', '/18-plus', '/18plus',
]

def is_adult_content(title, url=''):
    title_lower = title.lower()
    url_lower   = url.lower()
    for kw in ADULT_KEYWORDS:
        if kw in title_lower:
            log.info(f'  Blocked adult content: {title!r} (keyword: {kw!r})')
            return True
    for kw in ADULT_URL_KEYWORDS:
        if kw in url_lower:
            log.info(f'  Blocked adult URL: {url!r} (keyword: {kw!r})')
            return True
    return False

def _make_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['GET'],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session

http = _make_session()

GENRE_MAP = {
    'Korean':    ['korean', 'k-drama', 'kdrama'],
    'Chinese':   ['chinese', 'china', 'mandarin', 'cdrama'],
    'Nollywood': ['nollywood', 'nigerian', 'yoruba', 'igbo', 'hausa', 'naija'],
    'Animation': ['animation', 'anime', 'cartoon', 'animated'],
    'Horror':    ['horror', 'haunted', 'demon', 'evil', 'ghost', 'curse'],
    'Thriller':  ['thriller', 'suspense', 'conspiracy'],
    'Crime':     ['crime', 'heist', 'gangster', 'mafia', 'drug'],
    'Sci-Fi':    ['sci-fi', 'scifi', 'alien', 'space', 'robot'],
    'Action':    ['action', 'fight', 'war', 'battle', 'mission', 'agent'],
    'Romance':   ['romance', 'love', 'wedding', 'marriage'],
    'Fantasy':   ['fantasy', 'magic', 'wizard', 'dragon', 'kingdom'],
    'Family':    ['family', 'kids', 'children'],
    'Adventure': ['adventure', 'journey', 'quest'],
    'Mystery':   ['mystery', 'detective', 'investigation', 'missing'],
    'History':   ['history', 'historical', 'ancient', 'medieval'],
    'Comedy':    ['comedy', 'funny', 'humor', 'laugh'],
    'Drama':     ['drama'],
}

TMDB_GENRE_MAP = {
    28:    'Action',
    12:    'Adventure',
    16:    'Animation',
    35:    'Comedy',
    80:    'Crime',
    99:    'Drama',
    18:    'Drama',
    10751: 'Family',
    14:    'Fantasy',
    36:    'History',
    27:    'Horror',
    10402: 'Drama',
    9648:  'Mystery',
    10749: 'Romance',
    878:   'Sci-Fi',
    53:    'Thriller',
    10752: 'Action',
    37:    'Drama',
}

URL_GENRE_MAP = {
    'korean-drama':   'Korean',
    'korean-movie':   'Korean',
    'chinese-drama':  'Chinese',
    'chinese-movie':  'Chinese',
    'japanese-drama': 'Drama',
    'anime-series':   'Animation',
    'anime':          'Animation',
    'nollywood':      'Nollywood',
    'horror':         'Horror',
    'thriller':       'Thriller',
    'action':         'Action',
    'romance':        'Romance',
    'sci-fi':         'Sci-Fi',
    'documentary':    'Drama',
    'animation':      'Animation',
    'bollywood':      'Drama',
    'hollywood':      'Action',
    'south-indian':   'Drama',
    'hindi-dubbed':   'Drama',
    'web-series':     'Drama',
}

DEAD_POSTER_DOMAINS = [
    'thenkiri.com',
    'nkiri.com',
    'loadedfiles.org',
]

def _is_safe_poster(url):
    if not url:
        return False
    url_lower = url.lower()
    return not any(domain in url_lower for domain in DEAD_POSTER_DOMAINS)

def _is_tmdb_poster(url):
    return bool(url and 'image.tmdb.org' in url)

def detect_genre_from_url(url):
    url_lower = url.lower()
    for key, genre in URL_GENRE_MAP.items():
        if key in url_lower:
            return genre
    return None

def detect_genre_from_title(title):
    tl = title.lower()
    for genre, keywords in GENRE_MAP.items():
        if any(kw in tl for kw in keywords):
            return genre
    return 'Drama'

def detect_year_from_text(*sources):
    for text in sources:
        if not text:
            continue
        match = re.search(r'(20\d{2}|19\d{2})', text)
        if match:
            yr = int(match.group(1))
            if yr <= CURRENT_YEAR + 1:
                return yr
    return None

def slugify(text):
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = text.strip('-')
    return text or 'untitled'

def clean_title_for_search(title):
    title = re.sub(r'\(.*?\)', '', title)
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(
        r'\b(480p|720p|1080p|4k|hd|ts|cam|bluray|webrip)\b', '',
        title, flags=re.IGNORECASE
    )
    title = re.sub(r'(20\d{2}|19\d{2})', '', title)
    title = re.sub(
        r'\b(korean drama|korean movie|chinese drama|chinese movie|'
        r'japanese drama|anime series|nollywood movie|nollywood film|'
        r'hollywood movie|bollywood movie|web series|tv series|'
        r'complete series|complete season)\b.*$',
        '', title, flags=re.IGNORECASE
    )
    title = re.sub(r'\s+', ' ', title)
    return title.strip()

SERIES_PATTERNS = [
    r's\d{1,2}\s*e\d{1,2}',
    r's\d{1,2}\b',
    r'season\s*\d+',
    r'episode\s*\d+',
    r'complete\s*series',
    r'\bbatch\b',
    r'\bep\s*\d+\b',
    r'\bpart\s*\d+\b',
    r'- series\b',
    r'\bseries\s*\d+\b',
    r'complete\s*tv\s*series',
    r'complete\s*korean\s*drama',
    r'complete\s*anime\s*series',
    r'complete\s*chinese\s*drama',
    r'complete\s*japanese\s*drama',
]

def is_series(title):
    return any(re.search(p, title.lower()) for p in SERIES_PATTERNS)

def is_series_from_url(url):
    url_lower = url.lower()
    return any(p in url_lower for p in [
        'tv-series', 'complete-series', 'korean-drama',
        'chinese-drama', 'anime-series', 'japanese-drama',
        'complete-tv', 'complete-korean', 'complete-anime',
        'complete-chinese', 'complete-japanese', 'web-series',
    ])

def extract_season_episode(title):
    tl = title.lower()
    m = re.search(r's(\d{1,2})\s*e(\d{1,2})', tl)
    if m:
        return int(m.group(1)), int(m.group(2)), False

    season  = None
    episode = None

    sm = re.search(r'season\s*(\d+)', tl)
    if sm:
        season = int(sm.group(1))

    s_only = re.search(r'\bs(\d{1,2})\b', tl)
    if s_only and not season:
        season = int(s_only.group(1))

    em = re.search(r'episode\s*(\d+)', tl)
    if not em:
        em = re.search(r'\bep\s*(\d+)\b', tl)
    if em:
        episode = int(em.group(1))

    pm = re.search(r'\bpart\s*(\d+)\b', tl)
    if pm and not episode:
        episode = int(pm.group(1))

    season  = season or 1
    is_full = episode is None
    episode = episode if episode is not None else 0

    return season, episode, is_full

def clean_series_title(title):
    title = re.sub(r'\bS\d{1,2}\s*E\d{1,2}.*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'season\s*\d+.*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'episode\s*\d+.*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\bep\s*\d+.*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\bpart\s*\d+.*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\bs\d{1,2}\b.*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'complete\s*(tv\s*)?series.*', '', title, flags=re.IGNORECASE)
    title = re.sub(
        r'complete\s*(korean|chinese|anime|japanese)?\s*(drama|series).*',
        '', title, flags=re.IGNORECASE
    )
    title = re.sub(r'batch.*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'- series.*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'series\s*\d+.*', '', title, flags=re.IGNORECASE)
    title = re.sub(
        r'\b(korean drama|korean movie|chinese drama|chinese movie|'
        r'japanese drama|anime series|nollywood movie|nollywood film|'
        r'hollywood movie|web series)\b.*$',
        '', title, flags=re.IGNORECASE
    )
    title = re.sub(r'\(.*?\)', '', title)
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(r'\|\s*download.*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'^download\s*', '', title, flags=re.IGNORECASE)
    return title.strip(' -–:|')

def clean_movie_title(title):
    title = re.sub(r'\|\s*download.*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'^download\s*', '', title, flags=re.IGNORECASE)
    title = re.sub(
        r'\b(hollywood|nollywood|korean|chinese|anime|japanese|foreign|bollywood|south\s*indian)\s+(movie|drama|film)\b',
        '', title, flags=re.IGNORECASE
    )
    title = re.sub(r'\s+', ' ', title)
    return title.strip(' -–:|')

def _default_state_file(name):
    local_dir = Path(__file__).parent / 'crawler_state'
    try:
        local_dir.mkdir(parents=True, exist_ok=True)
        return str(local_dir / name)
    except OSError:
        return str(Path(tempfile.gettempdir()) / name)

def _load_processed_urls(state_file):
    p = Path(state_file)
    if not p.exists():
        return set()
    return {line.strip() for line in p.read_text(encoding='utf-8').splitlines() if line.strip()}

def _mark_url_processed(state_file, url):
    with open(state_file, 'a', encoding='utf-8') as f:
        f.write(url + '\n')

DLDOWNLOAD_STATE   = os.getenv('DLDOWNLOAD_STATE_FILE',   _default_state_file('dldownload_processed.txt'))
THENKIRI_STATE     = os.getenv('THENKIRI_STATE_FILE',     _default_state_file('thenkiri_processed.txt'))
LOADEDFILES_STATE  = os.getenv('LOADEDFILES_STATE_FILE',  _default_state_file('loadedfiles_processed.txt'))

_tmdb_lock      = threading.Lock()
_tmdb_last_call = 0.0
TMDB_MIN_INTERVAL = 0.05

def tmdb_search(title, year=None, prefer_tv=False):
    global _tmdb_last_call

    if not TMDB_KEY:
        log.warning('No TMDB API key found')
        return None

    with _tmdb_lock:
        elapsed = time.time() - _tmdb_last_call
        if elapsed < TMDB_MIN_INTERVAL:
            time.sleep(TMDB_MIN_INTERVAL - elapsed)
        _tmdb_last_call = time.time()

    clean = clean_title_for_search(title)

    try:
        params = {
            'api_key':  TMDB_KEY,
            'query':    clean,
            'language': 'en-US',
            'page':     1
        }

        def parse_movie(r):
            poster    = f"{TMDB_IMG}{r['poster_path']}" if r.get('poster_path') else None
            genre_ids = r.get('genre_ids', [])
            genre     = TMDB_GENRE_MAP.get(genre_ids[0], 'Drama') if genre_ids else 'Drama'
            release   = r.get('release_date', '')
            return {
                'poster':      poster,
                'description': r.get('overview', '')[:500],
                'genre':       genre,
                'year':        int(release[:4]) if release else (year or CURRENT_YEAR)
            }

        def parse_tv(r):
            poster    = f"{TMDB_IMG}{r['poster_path']}" if r.get('poster_path') else None
            genre_ids = r.get('genre_ids', [])
            genre     = TMDB_GENRE_MAP.get(genre_ids[0], 'Drama') if genre_ids else 'Drama'
            air_date  = r.get('first_air_date', '')
            return {
                'poster':      poster,
                'description': r.get('overview', '')[:500],
                'genre':       genre,
                'year':        int(air_date[:4]) if air_date else (year or CURRENT_YEAR)
            }

        def _get(endpoint, p):
            global _tmdb_last_call
            res = http.get(f'{TMDB_BASE}/{endpoint}', params=p, timeout=10)
            if res.status_code == 429:
                retry_after = int(res.headers.get('Retry-After', 5))
                log.warning(f'TMDB rate limit hit — sleeping {retry_after}s')
                time.sleep(retry_after)
                with _tmdb_lock:
                    _tmdb_last_call = time.time()
                res = http.get(f'{TMDB_BASE}/{endpoint}', params=p, timeout=10)
            return res.json()

        if prefer_tv:
            data = _get('search/tv', params)
            if data.get('results'):
                return parse_tv(data['results'][0])

        if year:
            params['year'] = year
        data = _get('search/movie', params)
        if data.get('results'):
            return parse_movie(data['results'][0])

        params.pop('year', None)
        data = _get('search/movie', params)
        if data.get('results'):
            return parse_movie(data['results'][0])

        data = _get('search/tv', params)
        if data.get('results'):
            return parse_tv(data['results'][0])

        return None

    except Exception as e:
        log.error(f'TMDB error for "{title}": {e}')
        return None

def _safe_get(url, timeout=20, session=None):
    requester = session or http
    try:
        res = requester.get(url, headers=HEADERS, timeout=timeout)
        content_type = res.headers.get('Content-Type', '')
        if res.status_code != 200:
            log.warning(f'HTTP {res.status_code} for {url}')
            return None
        if 'text' not in content_type and 'xml' not in content_type:
            log.warning(f'Unexpected Content-Type "{content_type}" for {url}')
            return None
        return res
    except Exception as e:
        log.error(f'Request failed for {url}: {e}')
        return None


def scrape_dldownload_page(url):
    res = _safe_get(url)
    if not res:
        return None

    try:
        soup = BeautifulSoup(res.text, 'lxml')

        title = None
        for sel in ['h2.entry-title', 'h1.entry-title', '.sdm_post_title', 'h1']:
            tag = soup.select_one(sel)
            if tag:
                title = tag.get_text(strip=True)
                break
        if not title:
            return None

        title = re.sub(r'\s+', ' ', title).strip()

        if is_adult_content(title, url):
            return None

        download_links = []
        seen = set()

        for a in soup.select('a.sdm_download, .sdm_download_link a'):
            href = a.get('href', '').strip()
            if not href or href in seen:
                continue
            label = a.get('title') or a.get_text(strip=True) or title

            quality = '720p'
            for q in ['2160p', '4k', '1080p', '720p', '480p', '360p']:
                if q.lower() in (title + label).lower():
                    quality = q
                    break

            download_links.append({
                'label': quality,
                'url':   href,
                'host':  'DLDownload',
                'title': label
            })
            seen.add(href)

        return {
            'title':  title,
            'links':  download_links,
            'url':    url,
            'source': 'dldownload'
        }

    except Exception as e:
        log.error(f'Error parsing {url}: {e}')
        return None

def get_dldownload_urls(max_urls=500):
    sitemap_url = f'{DLDOWNLOAD_BASE}/wp-sitemap-posts-sdm_downloads-1.xml'
    res = _safe_get(sitemap_url, timeout=15)
    if not res:
        log.error('Could not fetch dldownload sitemap')
        return []

    try:
        soup = BeautifulSoup(res.text, 'xml')
        locs = soup.find_all('loc')
        log.info(f'dldownload: Found {len(locs)} URLs')
        all_urls = [loc.text.strip() for loc in locs]
        all_urls.reverse()
        return all_urls[:max_urls]
    except Exception as e:
        log.error(f'dldownload sitemap parse error: {e}')
        return []


def _extract_poster_from_url_tag(url_tag, page_url):
    IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.webp')

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


def _get_entries_from_sitemaps(sitemaps, max_urls, source_name, fetch_fn=None):
    if fetch_fn is None:
        fetch_fn = _safe_get

    entries   = []
    seen_urls = set()

    for sitemap_url in sitemaps:
        if len(entries) >= max_urls:
            break

        res = fetch_fn(sitemap_url, timeout=15)
        if not res:
            log.error(f'Could not fetch {source_name} sitemap: {sitemap_url}')
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

                if any(x in page_url for x in ['/page/', '/category/', '/tag/', '/author/']):
                    continue

                if is_adult_content('', page_url):
                    continue

                raw_poster = _extract_poster_from_url_tag(url_tag, page_url)
                poster = raw_poster if _is_safe_poster(raw_poster) else None

                slug_part = page_url.rstrip('/').split('/')[-1]
                raw_title = slug_part.replace('-', ' ').title()

                if is_adult_content(raw_title, page_url):
                    continue

                entries.append({
                    'title':  raw_title,
                    'url':    page_url,
                    'poster': poster,
                    'source': source_name
                })

        except Exception as e:
            log.error(f'{source_name} sitemap parse error ({sitemap_url}): {e}')

        log.info(f'  Got {len(entries)} {source_name} entries so far')
        time.sleep(SLEEP_SITEMAP)

    log.info(f'Total {source_name} entries fetched: {len(entries)}')
    return entries


def get_thenkiri_entries(max_urls=500, sitemaps=None):
    if sitemaps is None:
        sitemaps = list(THENKIRI_SITEMAPS)
    return _get_entries_from_sitemaps(sitemaps, max_urls, 'thenkiri')


def get_loadedfiles_entries(max_urls=500, sitemaps=None):
    if sitemaps is None:
        sitemaps = list(LOADEDFILES_SITEMAPS)
    return _get_entries_from_sitemaps(sitemaps, max_urls, 'loadedfiles')


def _scrape_generic_wp_page(url, source_name, fetch_fn=None):
    if fetch_fn is None:
        fetch_fn = _safe_get

    res = fetch_fn(url)
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
            title = re.sub(
                rf'\s*[|\-–]\s*.*?({re.escape(source_name)}).*$', '',
                title, flags=re.IGNORECASE
            )

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
                if img.startswith('http') and 'use-on-site' not in img and _is_safe_poster(img):
                    poster = img
                    break

        return {
            'title':       title.strip() if title else None,
            'description': description,
            'poster':      poster,
        }

    except Exception as e:
        log.error(f'{source_name} page scrape error {url}: {e}')
        return None


def scrape_thenkiri_page(url):
    return _scrape_generic_wp_page(url, 'thenkiri')


def scrape_loadedfiles_page(url):
    return _scrape_generic_wp_page(url, 'loadedfiles')


def save_series(data, tmdb, source='dldownload'):
    raw_title    = data['title']
    series_title = clean_series_title(raw_title) or raw_title
    slug         = slugify(series_title)

    if not slug or slug == 'untitled':
        log.warning(f'  Skipped series — unusable slug for title: {raw_title!r}')
        return

    if is_adult_content(series_title, data.get('url', '')):
        return

    season, ep, is_full_season = extract_season_episode(raw_title)

    poster      = (tmdb.get('poster') if tmdb else None) or data.get('poster')
    description = tmdb.get('description', '') if tmdb else ''
    genre = (
        (tmdb.get('genre') if tmdb else None)
        or detect_genre_from_url(data.get('url', ''))
        or detect_genre_from_title(series_title)
    )

    try:
        stmt = pg_insert(Series).values(
            title       = series_title,
            slug        = slug,
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
                    (Series.description == '', pg_insert(Series).excluded.description),
                    else_=Series.description
                ),
            }
        ).returning(Series.id, Series.title)

        result = db.session.execute(stmt)
        db.session.commit()
        row = result.fetchone()
        series_id = row[0]

        series = db.session.get(Series, series_id)
        if not series:
            log.warning(f'  Could not reload series id={series_id}')
            return

        log.info(f'  Series upserted: {series_title}')

    except Exception as e:
        db.session.rollback()
        log.error(f'  DB error upserting series "{series_title}": {e}')
        return

    HOST_LABELS = {
        'thenkiri':    'TheNkiri',
        'loadedfiles': 'LoadedFiles',
    }

    if data.get('links'):
        first  = data['links'][0]
        host   = first['host']
        ep_url = first['url']
    elif source in HOST_LABELS:
        host   = HOST_LABELS[source]
        ep_url = data['url']
    else:
        log.warning(f'  No download link for series "{series_title}" — series saved without episode')
        return

    try:
        if is_full_season:
            existing = Episode.query.filter_by(
                series_id=series.id, season=season, episode=0
            ).first()
            if not existing:
                episode = Episode(
                    series_id = series.id,
                    season    = season,
                    episode   = 0,
                    title     = raw_title,
                    url       = ep_url,
                    host      = host
                )
                db.session.add(episode)
                log.info(f'  ✓ Full season pack → S{season:02d} of {series_title}')
            else:
                log.info(f'  Season pack exists: S{season:02d} of {series_title}')
        else:
            existing = Episode.query.filter_by(
                series_id=series.id, season=season, episode=ep
            ).first()
            if not existing:
                episode = Episode(
                    series_id = series.id,
                    season    = season,
                    episode   = ep,
                    title     = raw_title,
                    url       = ep_url,
                    host      = host
                )
                db.session.add(episode)
                log.info(f'  ✓ Episode S{season:02d}E{ep:02d} → {series_title}')
            else:
                log.info(f'  Episode exists: S{season:02d}E{ep:02d} of {series_title}')

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        log.error(f'  DB error saving episode for "{series_title}": {e}')


def save_movie(data, tmdb, source='dldownload'):
    title = data['title']
    slug  = slugify(title)

    if not slug or slug == 'untitled':
        log.warning(f'  Skipped movie — unusable slug for title: {title!r}')
        return

    if is_adult_content(title, data.get('url', '')):
        return

    poster      = (tmdb.get('poster') if tmdb else None) or data.get('poster')
    description = tmdb.get('description', '') if tmdb else ''
    genre = (
        (tmdb.get('genre') if tmdb else None)
        or detect_genre_from_url(data.get('url', ''))
        or detect_genre_from_title(title)
    )
    year = (
        (tmdb.get('year') if tmdb else None)
        or detect_year_from_text(title, data.get('url', ''))
        or CURRENT_YEAR
    )

    HOST_LABELS = {
        'thenkiri':    'TheNkiri',
        'loadedfiles': 'LoadedFiles',
    }

    try:
        stmt = pg_insert(Movie).values(
            title       = title,
            slug        = slug,
            poster_url  = poster,
            year        = year,
            genre       = genre,
            description = description,
            badge       = 'New',
            is_trending = False,
        ).on_conflict_do_update(
            index_elements=['slug'],
            set_={
                'poster_url': db.case(
                    (Movie.poster_url == None, pg_insert(Movie).excluded.poster_url),
                    (
                        db.and_(
                            Movie.poster_url.notlike('%image.tmdb.org%'),
                            pg_insert(Movie).excluded.poster_url.like('%image.tmdb.org%')
                        ),
                        pg_insert(Movie).excluded.poster_url
                    ),
                    else_=Movie.poster_url
                ),
                'description': db.case(
                    (Movie.description == None, pg_insert(Movie).excluded.description),
                    (Movie.description == '', pg_insert(Movie).excluded.description),
                    else_=Movie.description
                ),
            }
        ).returning(Movie.id, Movie.title)

        result   = db.session.execute(stmt)
        db.session.flush()
        row      = result.fetchone()
        movie_id = row[0]

        existing_links = DownloadLink.query.filter_by(movie_id=movie_id).count()
        if existing_links == 0:
            if data.get('links'):
                for link_data in data['links']:
                    link = DownloadLink(
                        movie_id = movie_id,
                        label    = link_data['label'],
                        url      = link_data['url'],
                        host     = link_data['host']
                    )
                    db.session.add(link)
            elif source in HOST_LABELS:
                link = DownloadLink(
                    movie_id = movie_id,
                    label    = data.get('quality', 'Download'),
                    url      = data['url'],
                    host     = HOST_LABELS[source]
                )
                db.session.add(link)

        db.session.commit()
        log.info(
            f'  ✓ Movie: {title} [{genre}] '
            f'| poster: {"✓" if poster else "✗"} '
            f'| source: {source}'
        )

    except Exception as e:
        db.session.rollback()
        log.error(f'  DB error saving movie "{title}": {e}')


def _run_sitemap_crawl(
    source_name,
    state_file,
    get_entries_fn,
    scrape_page_fn,
    max_urls,
    fetch_pages,
    sleep_loop,
    sleep_page,
):
    log.info(f'═══ {source_name} crawl ═══')
    total_movies  = 0
    total_series  = 0
    total_skipped = 0
    total_blocked = 0

    processed = _load_processed_urls(state_file)
    log.info(f'Already processed: {len(processed)} URLs')

    entries = get_entries_fn(max_urls=max_urls)
    if not entries:
        log.error(f'No entries from {source_name} sitemaps.')
        return

    entries = [e for e in entries if e['url'] not in processed]
    log.info(f'Processing {len(entries)} new {source_name} entries...')

    for i, entry in enumerate(entries, 1):
        log.info(f'[{i}/{len(entries)}] {entry["url"]}')

        title  = entry['title']
        poster = entry['poster']

        if fetch_pages:
            page_data = scrape_page_fn(entry['url'])
            if page_data is None:
                total_blocked += 1
                _mark_url_processed(state_file, entry['url'])
                continue
            if page_data.get('title'):
                title = clean_movie_title(page_data['title'])
            if page_data.get('poster'):
                poster = page_data['poster']
            if page_data.get('description'):
                entry['description'] = page_data['description']
            time.sleep(sleep_page)

        if is_adult_content(title, entry['url']):
            total_blocked += 1
            _mark_url_processed(state_file, entry['url'])
            continue

        title_is_series = is_series(title) or is_series_from_url(entry['url'])
        search_title = clean_series_title(title) if title_is_series else clean_movie_title(title)

        if not search_title:
            log.info('  Skipped — empty title after cleaning')
            total_skipped += 1
            _mark_url_processed(state_file, entry['url'])
            continue

        year = detect_year_from_text(title, entry['url'])
        tmdb = tmdb_search(search_title, year=year, prefer_tv=title_is_series)

        if tmdb and not tmdb.get('poster') and poster:
            tmdb['poster'] = poster
        elif not tmdb:
            tmdb = {
                'poster':      poster,
                'description': '',
                'genre':       (
                    detect_genre_from_url(entry['url'])
                    or detect_genre_from_title(title)
                ),
                'year': year or CURRENT_YEAR
            }

        log.info(
            f'  TMDB: {"found" if tmdb else "not found"} '
            f'| poster: {"✓" if tmdb and tmdb.get("poster") else "✗"}'
        )

        data = {
            'title':  search_title,
            'url':    entry['url'],
            'poster': poster,
            'links':  []
        }

        if title_is_series:
            save_series(data, tmdb, source=source_name)
            total_series += 1
        else:
            save_movie(data, tmdb, source=source_name)
            total_movies += 1

        _mark_url_processed(state_file, entry['url'])
        time.sleep(sleep_loop)

    log.info(
        f'{source_name} done: {total_movies} movies | '
        f'{total_series} series | {total_skipped} skipped | '
        f'{total_blocked} adult blocked'
    )


def run_dldownload_crawl(max_urls=100):
    log.info('═══ DLDownload crawl ═══')
    total_movies  = 0
    total_series  = 0
    total_skipped = 0
    total_blocked = 0

    processed = _load_processed_urls(DLDOWNLOAD_STATE)
    log.info(f'Already processed: {len(processed)} URLs')

    post_urls = get_dldownload_urls(max_urls=max_urls)
    if not post_urls:
        log.error('No URLs found in dldownload sitemap.')
        return

    post_urls = [u for u in post_urls if u not in processed]
    log.info(f'Crawling {len(post_urls)} new dldownload URLs...')

    for i, url in enumerate(post_urls, 1):
        log.info(f'[{i}/{len(post_urls)}] {url}')

        if is_adult_content('', url):
            total_blocked += 1
            _mark_url_processed(DLDOWNLOAD_STATE, url)
            continue

        data = scrape_dldownload_page(url)
        if not data:
            log.info('  Skipped — could not scrape or blocked')
            total_skipped += 1
            _mark_url_processed(DLDOWNLOAD_STATE, url)
            continue

        if not data['links']:
            log.info(f'  No download links: {data["title"]}')
            total_skipped += 1
            _mark_url_processed(DLDOWNLOAD_STATE, url)
            continue

        title_is_series = is_series(data['title'])
        year = detect_year_from_text(data['title'], url)
        tmdb = tmdb_search(
            clean_series_title(data['title']) if title_is_series else data['title'],
            year=year,
            prefer_tv=title_is_series
        )

        log.info(
            f'  TMDB: {"found" if tmdb else "not found"} '
            f'| poster: {"✓" if tmdb and tmdb.get("poster") else "✗"}'
        )

        if title_is_series:
            save_series(data, tmdb, source='dldownload')
            total_series += 1
        else:
            save_movie(data, tmdb, source='dldownload')
            total_movies += 1

        _mark_url_processed(DLDOWNLOAD_STATE, url)
        time.sleep(SLEEP_DLDOWNLOAD)

    log.info(
        f'DLDownload done: {total_movies} movies | '
        f'{total_series} series | {total_skipped} skipped | '
        f'{total_blocked} adult blocked'
    )


def run_thenkiri_crawl(max_urls=200, fetch_pages=False):
    _run_sitemap_crawl(
        source_name    = 'thenkiri',
        state_file     = THENKIRI_STATE,
        get_entries_fn = get_thenkiri_entries,
        scrape_page_fn = scrape_thenkiri_page,
        max_urls       = max_urls,
        fetch_pages    = fetch_pages,
        sleep_loop     = SLEEP_THENKIRI_LOOP,
        sleep_page     = SLEEP_THENKIRI_PAGE,
    )


def run_loadedfiles_crawl(max_urls=200, fetch_pages=False):
    _run_sitemap_crawl(
        source_name    = 'loadedfiles',
        state_file     = LOADEDFILES_STATE,
        get_entries_fn = get_loadedfiles_entries,
        scrape_page_fn = scrape_loadedfiles_page,
        max_urls       = max_urls,
        fetch_pages    = fetch_pages,
        sleep_loop     = SLEEP_LOADEDFILES_LOOP,
        sleep_page     = SLEEP_LOADEDFILES_PAGE,
    )


def run_crawl(
    max_urls=100,
    include_dldownload=True,
    include_thenkiri=True,
    include_loadedfiles=True,
    thenkiri_max=200,
    loadedfiles_max=200,
    fetch_thenkiri_pages=False,
    fetch_loadedfiles_pages=False,
):
    from flask import current_app
    app = current_app._get_current_object()

    log.info('═══ Starting 9janetmovies crawl ═══')

    def _dldownload_worker():
        with app.app_context():
            run_dldownload_crawl(max_urls)

    def _thenkiri_worker():
        with app.app_context():
            run_thenkiri_crawl(thenkiri_max, fetch_thenkiri_pages)

    def _loadedfiles_worker():
        with app.app_context():
            run_loadedfiles_crawl(loadedfiles_max, fetch_loadedfiles_pages)

    futures = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        if include_dldownload:
            futures.append(executor.submit(_dldownload_worker))
        if include_thenkiri:
            futures.append(executor.submit(_thenkiri_worker))
        if include_loadedfiles:
            futures.append(executor.submit(_loadedfiles_worker))
        for f in as_completed(futures):
            exc = f.exception()
            if exc:
                log.error(f'Crawl thread failed: {exc}')

    log.info('═══ All crawls complete ═══')


def backfill_descriptions(batch_size=500, offset=0):
    log.info(f'═══ Backfill descriptions (offset={offset}, batch={batch_size}) ═══')
    updated_movies  = 0
    updated_series  = 0
    skipped         = 0

    movies = Movie.query.filter(
        (Movie.description == None) | (Movie.description == '') |
        (Movie.poster_url == None) |
        (Movie.poster_url.notlike('%image.tmdb.org%'))
    ).order_by(Movie.id).offset(offset).limit(batch_size).all()

    log.info(f'Movies needing update: {len(movies)}')

    for movie in movies:
        tmdb = tmdb_search(
            clean_title_for_search(movie.title),
            year=movie.year,
            prefer_tv=False
        )
        if not tmdb:
            tmdb = tmdb_search(clean_title_for_search(movie.title), prefer_tv=True)

        if tmdb and (tmdb.get('description') or tmdb.get('poster')):
            changed = False
            if tmdb.get('description') and not movie.description:
                movie.description = tmdb['description']
                changed = True
            if tmdb.get('poster') and (
                not movie.poster_url or
                'image.tmdb.org' not in movie.poster_url
            ):
                movie.poster_url = tmdb['poster']
                changed = True
            if changed:
                try:
                    db.session.commit()
                    updated_movies += 1
                    log.info(f'  ✓ Movie updated: {movie.title}')
                except Exception as e:
                    db.session.rollback()
                    log.error(f'  DB error for movie "{movie.title}": {e}')
            else:
                skipped += 1
        else:
            skipped += 1

        time.sleep(0.1)

    all_series = Series.query.filter(
        (Series.description == None) | (Series.description == '') |
        (Series.poster_url == None) |
        (Series.poster_url.notlike('%image.tmdb.org%'))
    ).order_by(Series.id).offset(offset).limit(batch_size).all()

    log.info(f'Series needing update: {len(all_series)}')

    for s in all_series:
        tmdb = tmdb_search(
            clean_title_for_search(s.title),
            prefer_tv=True
        )
        if not tmdb:
            tmdb = tmdb_search(clean_title_for_search(s.title), prefer_tv=False)

        if tmdb and (tmdb.get('description') or tmdb.get('poster')):
            changed = False
            if tmdb.get('description') and not s.description:
                s.description = tmdb['description']
                changed = True
            if tmdb.get('poster') and (
                not s.poster_url or
                'image.tmdb.org' not in s.poster_url
            ):
                s.poster_url = tmdb['poster']
                changed = True
            if changed:
                try:
                    db.session.commit()
                    updated_series += 1
                    log.info(f'  ✓ Series updated: {s.title}')
                except Exception as e:
                    db.session.rollback()
                    log.error(f'  DB error for series "{s.title}": {e}')
            else:
                skipped += 1
        else:
            skipped += 1

        time.sleep(0.1)

    log.info(
        f'Backfill done: {updated_movies} movies updated | '
        f'{updated_series} series updated | {skipped} skipped'
    )
    return updated_movies + updated_series


def backfill_all(batch_size=500):
    log.info('═══ Full backfill started ═══')
    offset = 0
    total  = 0
    while True:
        updated = backfill_descriptions(batch_size=batch_size, offset=offset)
        total  += updated
        if updated == 0:
            break
        offset += batch_size
    log.info(f'═══ Full backfill complete — {total} total records updated ═══')