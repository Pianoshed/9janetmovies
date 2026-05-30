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

RELEVANT_KEYWORDS = [
    'movie', 'film', 'nollywood', 'cinema', 'actress', 'actor',
    'celebrity', 'music', 'album', 'single', 'concert', 'award',
    'entertainment', 'tv', 'series', 'netflix', 'amazon', 'show',
    'gist', 'drama', 'rapper', 'singer', 'artiste', 'artist',
    'yoruba', 'igbo', 'hausa', 'naija', 'nigerian',
]

ADULT_KEYWORDS = [
    'porn', 'xxx', 'nude', 'naked', 'sex tape', 'erotic',
    'hardcore', 'onlyfans', 'adult content',
]

# Tags to strip from article content
JUNK_TAGS = [
    'script', 'style', 'iframe', 'form', 'nav', 'footer',
    'header', 'aside', 'button', 'input', 'select',
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
    if any(kw in combined for kw in ADULT_KEYWORDS):
        return False
    return any(kw in combined for kw in RELEVANT_KEYWORDS)


def extract_image(item_soup, entry_text=''):
    for tag in ['media:content', 'media:thumbnail']:
        media = item_soup.find(tag)
        if media and media.get('url', '').startswith('http'):
            return media['url']

    enc = item_soup.find('enclosure', type=lambda t: t and 'image' in t)
    if enc and enc.get('url', '').startswith('http'):
        return enc['url']

    if entry_text:
        img = BeautifulSoup(entry_text, 'lxml').find('img')
        if img and img.get('src', '').startswith('http'):
            return img['src']

    return None


def parse_date(item_soup):
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


def fetch_full_content(url):
    """
    Fetch the full article page and extract clean readable content.
    Returns (content_html, image_url) tuple.
    """
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return None, None

        soup = BeautifulSoup(res.text, 'lxml')

        # Try to get og:image first
        image_url = None
        og_img = soup.find('meta', property='og:image')
        if og_img and og_img.get('content', '').startswith('http'):
            image_url = og_img['content']

        # Find the main article content
        article = None
        for selector in [
            'article',
            '.post-body',
            '.entry-content',
            '.post-content',
            '.article-body',
            '.story-body',
            '.content-body',
            'main',
        ]:
            article = soup.select_one(selector)
            if article:
                break

        if not article:
            return None, image_url

        # Remove junk tags
        for tag in article.find_all(JUNK_TAGS):
            tag.decompose()

        # Remove social share / subscribe divs
        for el in article.find_all(class_=re.compile(
            r'share|social|subscribe|newsletter|related|comment|ad|widget|sidebar',
            re.IGNORECASE
        )):
            el.decompose()

        # Extract clean paragraphs as HTML
        paragraphs = []
        for tag in article.find_all(['p', 'h2', 'h3', 'h4', 'blockquote', 'ul', 'ol']):
            text = tag.get_text(strip=True)
            if len(text) < 20:
                continue
if any(kw in text.lower() for kw in ADULT_KEYWORDS):
    continue

JUNK_PHRASES = [
    'read also', 'follow us', 'follow legit', 'find it fast',
    'subscribe', 'newsletter', 'breaking news to viral',
    'click here', 'source:', 'tags:', 'hot:', 'authors:',
    'contact:', 'compiled some', 'read the comments',
    'commented:', ' said:', 'reactions that trailed',
    'legit.ng reported', 'legit.ng also', 'also reported',
    'share on', 'send this', 'whatsapp', 'copy link',
]
        if any(phrase in text.lower() for phrase in JUNK_PHRASES):
            continue
        if len(text) < 40:
            continue
            # Keep as simple HTML
            if tag.name == 'p':
                paragraphs.append(f'<p>{text}</p>')
            elif tag.name in ['h2', 'h3', 'h4']:
                paragraphs.append(f'<{tag.name}>{text}</{tag.name}>')
            elif tag.name == 'blockquote':
                paragraphs.append(f'<blockquote>{text}</blockquote>')
            elif tag.name in ['ul', 'ol']:
                items = ''.join(
                    f'<li>{li.get_text(strip=True)}</li>'
                    for li in tag.find_all('li')
                    if li.get_text(strip=True)
                )
                if items:
                    paragraphs.append(f'<{tag.name}>{items}</{tag.name}>')

        content = '\n'.join(paragraphs)
        return content if len(content) > 100 else None, image_url

    except Exception as e:
        log.error(f'  Full content fetch error {url}: {e}')
        return None, None


def save_post(title, url, summary, content, image_url, source_name, category, published_at):
    slug = slugify(title)
    if not slug or slug == 'untitled':
        return

    try:
        existing = BlogPost.query.filter(
            (BlogPost.slug == slug) | (BlogPost.source_url == url)
        ).first()

        if existing:
            # Update content if it was missing
            if not existing.content and content:
                existing.content = content
                db.session.commit()
            return

        post = BlogPost(
            title        = title[:300],
            slug         = slug,
            summary      = summary[:600] if summary else '',
            content      = content,
            image_url    = image_url,
            source_name  = source_name,
            source_url   = url,
            category     = category,
            published_at = published_at,
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

    for item in items[:30]:
        try:
            title_tag = item.find('title')
            link_tag  = item.find('link')

            if not title_tag or not link_tag:
                continue

            title = title_tag.get_text(strip=True)
            url   = link_tag.get_text(strip=True)

            if not title or not url:
                continue

            desc_tag = item.find('description') or item.find('content:encoded')
            raw_desc = desc_tag.get_text(strip=True) if desc_tag else ''
            summary  = BeautifulSoup(raw_desc, 'lxml').get_text(separator=' ')[:600].strip()

            if not is_relevant(title, summary):
                continue

            # Fetch full article content from the page
            content, page_image = fetch_full_content(url)
            image_url = extract_image(item, raw_desc) or page_image
            published_at = parse_date(item)

            save_post(
                title        = title,
                url          = url,
                summary      = summary,
                content      = content,
                image_url    = image_url,
                source_name  = name,
                category     = category,
                published_at = published_at,
            )
            count += 1
            time.sleep(0.5)  # slightly longer delay since we're fetching full pages

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

    # Keep only the latest 200 posts
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