import os
import re
import time
import logging
import requests
from app import db
from app.models.movie import Movie
from app.models.download_link import DownloadLink
from app.crawler.dldownload import (
    slugify, detect_genre_from_title,
    tmdb_search, clean_title_for_search, CURRENT_YEAR
)

log = logging.getLogger(__name__)

YOUTUBE_API_KEY  = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_SEARCH   = 'https://www.googleapis.com/youtube/v3/search'
YOUTUBE_VIDEOS   = 'https://www.googleapis.com/youtube/v3/videos'

NOLLYWOOD_QUERIES = [
    'Nollywood full movie 2025',
    'Nigerian movie 2025 full movie',
    'Yoruba movie 2025 full movie',
    'Igbo movie 2025 full movie',
    'Nollywood blockbuster 2024 full movie',
    'Latest Nollywood movie free',
    'Nigerian comedy movie 2025',
    'Nollywood action movie 2025',
    'Nollywood romance movie 2025',
    'Nollywood horror movie 2025',
]

# ── CLEAN YOUTUBE DESCRIPTION ─────────────────────────────────
def clean_description(text):
    if not text:
        return ''
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'#\w+', '', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    lines = [l for l in lines if not any(x in l.lower() for x in [
        'subscribe', 'follow us', 'like and share', 'youtube',
        'instagram', 'facebook', 'twitter', 'tiktok', 'whatsapp',
        'telegram', 'click here', 'watch more', 'for more',
        'comment below', 'turn on notification', 'hit the bell',
    ])]
    return ' '.join(lines)[:500].strip()

# ── CLEAN YOUTUBE TITLE ───────────────────────────────────────
def clean_youtube_title(title):
    title = re.sub(r'\(.*?\)', '', title)
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(
        r'\b(full movie|latest|official|hd|4k|free|nollywood|nigerian|yoruba|igbo)\b',
        '', title, flags=re.IGNORECASE
    )
    title = re.sub(r'\d{4}', '', title)
    title = re.sub(r'\s+', ' ', title)
    return title.strip(' -–:|')

# ── SEARCH YOUTUBE ────────────────────────────────────────────
def search_youtube(query, max_results=20):
    try:
        params = {
            'key':           YOUTUBE_API_KEY,
            'q':             query,
            'part':          'snippet',
            'type':          'video',
            'maxResults':    max_results,
            'videoDuration': 'long',
            'order':         'relevance',
        }
        res  = requests.get(YOUTUBE_SEARCH, params=params, timeout=10)
        data = res.json()
        return data.get('items', [])
    except Exception as e:
        log.error(f'YouTube search error: {e}')
        return []

# ── SAVE MOVIE ────────────────────────────────────────────────
def save_youtube_movie(raw_title, video_id, yt_poster, yt_description):
    title = clean_youtube_title(raw_title)
    slug  = slugify(title)

    if not slug or slug == 'untitled':
        log.warning(f'  Skipped — bad slug for: {raw_title!r}')
        return

    youtube_url = f'https://www.youtube.com/watch?v={video_id}'

    # TMDB lookup for better metadata
    tmdb = tmdb_search(clean_title_for_search(title))
    poster      = (tmdb.get('poster')      if tmdb else None) or yt_poster
    description = (tmdb.get('description') if tmdb else None) or clean_description(yt_description)
    genre       = (tmdb.get('genre')       if tmdb else None) or detect_genre_from_title(title) or 'Nollywood'
    year        = (tmdb.get('year')        if tmdb else None) or CURRENT_YEAR

    try:
        existing = Movie.query.filter_by(slug=slug).first()

        if existing:
            updated = False
            if not existing.poster_url and poster:
                existing.poster_url  = poster
                updated = True
            if not existing.description and description:
                existing.description = description
                updated = True
            if updated:
                db.session.commit()

            existing_hosts = [l.host for l in existing.download_links]
            if 'YouTube' not in existing_hosts:
                db.session.add(DownloadLink(
                    movie_id = existing.id,
                    label    = 'YouTube',
                    url      = youtube_url,
                    host     = 'YouTube'
                ))
                db.session.commit()
                log.info(f'  Added YouTube link to: {title}')
            else:
                log.info(f'  Already exists: {title}')
            return

        movie = Movie(
            title       = title,
            slug        = slug,
            poster_url  = poster,
            year        = year,
            genre       = genre,
            description = description,
            badge       = 'New',
            is_trending = False,
        )
        db.session.add(movie)
        db.session.flush()

        db.session.add(DownloadLink(
            movie_id = movie.id,
            label    = 'YouTube',
            url      = youtube_url,
            host     = 'YouTube'
        ))
        db.session.commit()
        log.info(f'  ✓ YouTube movie: {title} [{genre}] | poster: {"✓" if poster else "✗"}')

    except Exception as e:
        db.session.rollback()
        log.error(f'  DB error for "{title}": {e}')

# ── MAIN CRAWL ────────────────────────────────────────────────
def run_youtube_crawl(max_results_per_query=20):
    if not YOUTUBE_API_KEY:
        log.error('YOUTUBE_API_KEY not set')
        return

    log.info('═══ YouTube Nollywood crawl ═══')
    total = 0
    seen  = set()

    for query in NOLLYWOOD_QUERIES:
        log.info(f'Searching: "{query}"')
        items = search_youtube(query, max_results=max_results_per_query)

        for item in items:
            try:
                video_id = item['id'].get('videoId')
                if not video_id or video_id in seen:
                    continue
                seen.add(video_id)

                snippet     = item['snippet']
                raw_title   = snippet.get('title', '')
                description = snippet.get('description', '')
                poster      = snippet.get('thumbnails', {}).get('high', {}).get('url')

                save_youtube_movie(raw_title, video_id, poster, description)
                total += 1
                time.sleep(0.3)

            except Exception as e:
                log.error(f'Error processing item: {e}')
                continue

        time.sleep(1)

    log.info(f'═══ YouTube crawl done: {total} processed ═══')