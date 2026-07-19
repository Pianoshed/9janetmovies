"""
backfill_tmdb_posters.py

One-off script: finds Movie rows with a missing/empty poster_url,
re-queries TMDB, and fills them in.

Run from your Flask project root (same place you'd run `flask shell`
or your crawler), so `from app import ...` resolves correctly:

    python backfill_tmdb_posters.py

Requires:
    TMDB_API_KEY env var set (same one your crawler already uses)

Safe to re-run: it only touches rows where poster_url is NULL or ''.
"""

import os
import time
import requests

from flask import Flask
from app import db
from app.models.movie import Movie
from app.models.download_link import DownloadLink  # noqa: F401 — needed so SQLAlchemy can resolve Movie.links relationship

# Minimal app instance — deliberately does NOT use create_app(), so we skip
# admin/mail/limiter/blueprints and their extra dependencies (flask_admin,
# flask_mail, etc.) that aren't needed for a DB-only backfill script.
app = Flask(__name__)
app.config.from_object('app.config.Config')
db.init_app(app)

import re

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# Words/patterns commonly injected by download-site crawlers that break
# TMDB search matching. Add to this list as you spot more junk patterns.
JUNK_PATTERNS = [
    r"\bdownload\b",
    r"\bfull movie\b",
    r"\bwatch online\b",
    r"\b(hd|hdrip|webrip|web-dl|bluray|brrip|dvdrip|camrip|hdcam)\b",
    r"\b(mp4|mkv)\b",
    r"\b\d{3,4}p\b",          # e.g. 720p, 1080p
    r"\(\s*\)",                # leftover empty parens
    r"\bhollywood movie\b",
    r"\bforeign movie\b",
    r"\bhollywood documentary\b",
    r"\bdocumentary\b",
    r"\bspecial\b",
]


def clean_title_for_search(raw_title: str, year: int | None) -> str:
    """
    Strip crawler junk from a title before sending it to TMDB.
    e.g. "The Green Knight 2021 Download (2021)" -> "The Green Knight"
    """
    title = raw_title

    # Remove a trailing "(YYYY)" block
    title = re.sub(r"\(\s*\d{4}\s*\)", "", title)

    # Remove a standalone 4-digit year token (often duplicated from the real year)
    if year:
        title = re.sub(rf"\b{year}\b", "", title)
    else:
        title = re.sub(r"\b(19|20)\d{2}\b", "", title)

    # Strip junk keywords (case-insensitive)
    for pattern in JUNK_PATTERNS:
        title = re.sub(pattern, "", title, flags=re.IGNORECASE)

    # Collapse extra whitespace left behind
    title = re.sub(r"\s{2,}", " ", title).strip(" -|:")

    return title or raw_title  # fall back to raw title if we stripped everything

# Be polite to TMDB's rate limit
REQUEST_DELAY_SECONDS = 0.3


def search_tmdb(title: str, year: int | None):
    """
    Search TMDB for a movie by title (+ year if available).
    Returns the poster_path of the best match, or None.
    """
    if not TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY is not set in the environment")

    query_title = clean_title_for_search(title, year)
    if query_title != title:
        print(f"  cleaned title: '{title}' -> '{query_title}'")

    params = {
        "api_key": TMDB_API_KEY,
        "query": query_title,
        "include_adult": False,
    }
    if year:
        params["year"] = year

    try:
        resp = requests.get(TMDB_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  ! TMDB request failed for '{title}': {e}")
        return None

    results = resp.json().get("results") or []
    if not results:
        # Retry without year in case the year is slightly off / mismatched
        if year:
            params.pop("year")
            try:
                resp = requests.get(TMDB_SEARCH_URL, params=params, timeout=10)
                resp.raise_for_status()
                results = resp.json().get("results") or []
            except requests.RequestException:
                return None

    if not results:
        return None

    best = results[0]  # TMDB already sorts by relevance/popularity
    poster_path = best.get("poster_path")
    if not poster_path:
        return None

    return f"{TMDB_IMAGE_BASE}{poster_path}"


def backfill():
    with app.app_context():
        missing = Movie.query.filter(
            (Movie.poster_url.is_(None))
            | (Movie.poster_url == "")
            | (~Movie.poster_url.ilike("%image.tmdb.org%"))
        ).all()

        print(f"Found {len(missing)} movie(s) without a TMDB poster_url.\n")

        updated = 0
        skipped = 0
        BATCH_SIZE = 20  # commit every N rows so Supabase's pooler doesn't time out a huge open transaction

        for i, movie in enumerate(missing, start=1):
            print(f"[{movie.id}] {movie.title} ({movie.year or 'no year'})")

            try:
                poster_url = search_tmdb(movie.title, movie.year)
            except Exception as e:
                print(f"  ! error searching TMDB, skipping: {e}")
                skipped += 1
                continue

            if poster_url:
                movie.poster_url = poster_url
                db.session.add(movie)
                updated += 1
                print(f"  -> found: {poster_url}")
            else:
                skipped += 1
                print("  -> no TMDB match found, left as-is")

            if i % BATCH_SIZE == 0:
                try:
                    db.session.commit()
                    print(f"  --- committed batch (row {i}/{len(missing)}) ---")
                except Exception as e:
                    print(f"  ! commit failed for this batch, rolling back: {e}")
                    db.session.rollback()

            time.sleep(REQUEST_DELAY_SECONDS)

        # Final commit for any remainder smaller than BATCH_SIZE
        try:
            db.session.commit()
        except Exception as e:
            print(f"  ! final commit failed: {e}")
            db.session.rollback()

        print(f"\nDone. Updated {updated}, skipped {skipped} (no match).")


if __name__ == "__main__":
    backfill()