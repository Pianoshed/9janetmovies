import re
import time
import logging
import requests
import unicodedata
from datetime import datetime
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup
from app import db
from app.models.blog_post import BlogPost

log = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}

# ── RSS SOURCES ───────────────────────────────────────────────
SOURCES = [
    {
        'name':     'Linda Ikeji Blog',
        'rss':      'https://www.lindaikejisblog.com/feeds/posts/default?alt=rss',
        'category': 'Celebrity',
    },
    {
        'name':     'Pulse Nigeria',
        'rss':      'https://www.pulse.ng/rss',
        'category': 'General',
    },
    {
        'name':     'Legit.ng',
        'rss':      'https://www.legit.ng/rss/all.rss',
        'category': 'General',
    },
    {
        'name':     'BellaNaija',
        'rss':      'https://www.bellanaija.com/feed/',
        'category': 'Celebrity',
    },
    {
        'name':     'TheCable Entertainment',
        'rss':      'https://www.thecable.ng/category/lifestyle/entertainment/feed',
        'category': 'Entertainment',
    },
    {
        'name':     'Tooxclusive',
        'rss':      'https://tooxclusive.com/feed/',
        'category': 'Music',
    },
]

# ── KEYWORDS TO FILTER FOR RELEVANT CONTENT ───────────────────
RELEVANT_KEYWORDS = [
    'movie', 'film', 'nollywood', 'cinema', 'actress', 'actor',
    'celebrity', 'music', 'album', 'single', 'concert', 'award',
    'entertainment', 'tv', 'series', 'netflix', 'amazon', 'show',
    'gist', 'drama', 'rapper', 'singer', 'artiste', 'artist',
    'yoruba', 'igbo', 'hausa', 'naija', 'nigerian',
]

# ── ADULT CONTENT FILTER ──────────────────────────────────────
ADULT_KEYWORDS = [
    'porn', 'xxx', 'nude', 'naked', 'sex tape', 'erotic',
    'hardcore', 'onlyfans', 'adult content',
]


def slugify(text):
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = text.strip('-')
    return (text or 'untitled')[:300]


def is_relevant(title, summary=''):
    combined = (title + ' ' + (summary or '')).lower()
    # Block adult content
    if any(kw in combined for kw in ADULT_KEYWORDS):
        return False
    # Must match at least one relevant keyword
    return any(kw in combined for kw in RELEVANT_KEYWORDS)


def extract_image(item_soup, entry_text=''):
    """Try multiple strategies to find an image in an RSS item."""
    # 1. media:content or media:thumbnail
    for tag in ['media:content', 'media:thumbnail']:
        media = item_soup.find(tag)
        if media and media.get('url', '').startswith('http'):
            return media['url']

    # 2. enclosure tag
    enc = item_soup.find('enclosure', type=lambda t: t and 'image' in t)
    if enc and enc.get('url', '').startswith('http'):
        return enc['url']

    # 3. First <img> in description/content
    if entry_text:
        img = BeautifulSoup(entry_text, 'lxml').find('img')
        if img and img.get('src', '').startswith('http'):
            return img['src']

    return None


def parse_date(item_soup):
    """Parse pubDate from RSS item."""
    pub = item_soup.find('pubDate')
    if pub:
        try:
            return parsedate_to_datetime(pub.text.strip()).replace(tzinfo=None)
        except Exception:
            pass
    return datetime.utcnow()


def fetch_rss(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            log.warning(f'RSS fetch failed {res.status_code}: {url}')
            return None
        return res.text
    except Exception as e:
        log.error(f'RSS fetch error {url}: {e}')
        return None


def save_post(title, url, summary, image_url, source_name, category, published_at):
    """Save a blog post to the DB, skip if already exists."""
    slug = slugify(title)
    if not slug or slug == 'untitled':
        return

    try:
        existing = BlogPost.query.filter(
            (BlogPost.slug == slug) | (BlogPost.source_url == url)
        ).first()

        if existing:
            return

        post = BlogPost(
            title       = title[:300],
            slug        = slug,
            summary     = summary[:600] if summary else '',
            image_url   = image_url,
            source_name = source_name,
            source_url  = url,
            category    = category,
            published_at= published_at,
        )
        db.session.add(post)
        db.session.commit()
        log.info(f'  ✓ [{source_name}] {title[:60]}')

    except Exception as e:
        db.session.rollback()
        log.error(f'  DB error saving post "{title[:60]}": {e}')


def crawl_source(source):
    name     = source['name']
    rss_url  = source['rss']
    category = source['category']

    log.info(f'── Crawling: {name}')
    xml = fetch_rss(rss_url)
    if not xml:
        return 0

    soup  = BeautifulSoup(xml, 'xml')
    items = soup.find_all('item')
    count = 0

    for item in items[:30]:  # max 30 per source per run
        try:
            title_tag = item.find('title')
            link_tag  = item.find('link')

            if not title_tag or not link_tag:
                continue

            title = title_tag.get_text(strip=True)
            url   = link_tag.get_text(strip=True)

            if not title or not url:
                continue

            # Get description/summary
            desc_tag = item.find('description') or item.find('content:encoded')
            raw_desc = desc_tag.get_text(strip=True) if desc_tag else ''
            # Strip HTML tags from summary
            summary = BeautifulSoup(raw_desc, 'lxml').get_text(separator=' ')[:600].strip()

            # Filter for relevant content only
            if not is_relevant(title, summary):
                continue

            image_url    = extract_image(item, raw_desc)
            published_at = parse_date(item)

            save_post(
                title        = title,
                url          = url,
                summary      = summary,
                image_url    = image_url,
                source_name  = name,
                category     = category,
                published_at = published_at,
            )
            count += 1
            time.sleep(0.1)

        except Exception as e:
            log.error(f'  Error processing item from {name}: {e}')
            continue

    return count


def run_blog_crawl():
    log.info('═══ Blog crawl started ═══')
    total = 0

    for source in SOURCES:
        try:
            count = crawl_source(source)
            total += count
            log.info(f'  {source["name"]}: {count} new posts')
        except Exception as e:
            log.error(f'  Source failed {source["name"]}: {e}')
        time.sleep(1)

    # Keep only the latest 200 posts to avoid DB bloat
    try:
        latest_ids = [
            r.id for r in BlogPost.query
            .order_by(BlogPost.published_at.desc())
            .limit(200).all()
        ]
        if latest_ids:
            BlogPost.query.filter(~BlogPost.id.in_(latest_ids)).delete(
                synchronize_session=False
            )
            db.session.commit()
            log.info('  Pruned old blog posts — keeping latest 200')
    except Exception as e:
        db.session.rollback()
        log.error(f'  Pruning error: {e}')

    log.info(f'═══ Blog crawl done: {total} new posts ═══')