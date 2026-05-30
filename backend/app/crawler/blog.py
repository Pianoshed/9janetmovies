import re
import time
import logging
import requests
import urllib3
import unicodedata
from datetime import datetime
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup
from app import db
from app.models.blog_post import BlogPost

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'no-cache',
    'Referer': 'https://www.google.com/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

SOURCES = [
    # ── Celebrity / Gossip ─────────────────────────────────────────────────
    {
        'name':     'Linda Ikeji Blog',
        'rss':      'https://www.lindaikejisblog.com/feeds/posts/default?alt=rss',
        'category': 'Celebrity',
        'verify':   True,
    },
    {
        'name':     'SDK Celebrities',
        'rss':      'https://www.stelladimokokorkus.com/feeds/posts/default?alt=rss',
        'category': 'Celebrity',
        'verify':   True,
    },
    {
        'name':     'BellaNaija',
        'rss':      'https://www.bellanaija.com/feed/',
        'category': 'Celebrity',
        'verify':   False,
    },
    {
        'name':     'BellaNaija Nollywood',
        'rss':      'https://www.bellanaija.com/nollywood/feed/',
        'category': 'Nollywood',
        'verify':   False,
    },
    {
        'name':     'Kemi Filani',
        'rss':      'https://kemifilani.ng/feed/',
        'category': 'Celebrity',
        'verify':   True,
    },
    {
        'name':     'Instablog9ja',
        'rss':      'https://www.instablog9ja.com/feed/',
        'category': 'Celebrity',
        'verify':   True,
    },

    # ── Nollywood / Movies ────────────────────────────────────────────────
    {
        'name':     'Kemi Filani Movies',
        'rss':      'https://kemifilani.ng/movies/feed/',
        'category': 'Nollywood',
        'verify':   True,
    },

    # ── General Entertainment News ────────────────────────────────────────
    {
        'name':     'Legit.ng',
        'rss':      'https://www.legit.ng/rss/all.rss',
        'category': 'Entertainment',
        'verify':   True,
    },
    {
        'name':     'PM News Entertainment',
        'rss':      'https://pmnewsnigeria.com/category/entertainment/feed/',
        'category': 'Entertainment',
        'verify':   True,
    },
    {
        'name':     'Daily Post Nigeria',
        'rss':      'https://dailypost.ng/feed/',
        'category': 'Entertainment',
        'verify':   False,
    },
    {
        'name':     'Channels TV',
        'rss':      'https://www.channelstv.com/feed/',
        'category': 'Entertainment',
        'verify':   True,
    },
    {
        'name':     'The Punch',
        'rss':      'https://punchng.com/feed/',
        'category': 'Entertainment',
        'verify':   True,
    },
    {
        'name':     'Vanguard Nigeria',
        'rss':      'https://www.vanguardngr.com/feed/',
        'category': 'Entertainment',
        'verify':   True,
    },
    {
        'name':     'NNN Entertainment',
        'rss':      'https://nnn.ng/category/entertainment/feed/',
        'category': 'Entertainment',
        'verify':   True,
    },

    # ── Music ─────────────────────────────────────────────────────────────
    {
        'name':     'NotJustOk',
        'rss':      'https://www.notjustok.com/feed/',
        'category': 'Music',
        'verify':   True,
    },
    {
        'name':     'Tooxclusive',
        'rss':      'https://tooxclusive.com/feed/',
        'category': 'Music',
        'verify':   True,
    },
    {
        'name':     'Naijaloaded',
        'rss':      'https://naijaloaded.com.ng/feed/',
        'category': 'Music',
        'verify':   True,
    },
    {
        'name':     'Okhype',
        'rss':      'https://www.okhype.com/feed/',
        'category': 'Music',
        'verify':   True,
    },
    {
        'name':     '247NaijaBuzz',
        'rss':      'https://www.247naijabuzz.com/feed/',
        'category': 'Music',
        'verify':   True,
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

JUNK_TAGS = [
    'script', 'style', 'iframe', 'form', 'nav', 'footer',
    'header', 'aside', 'button', 'input', 'select',
]

JUNK_PHRASES = [
    'read also', 'follow us', 'follow legit', 'find it fast',
    'subscribe', 'newsletter', 'click here', 'source:', 'tags:',
    'contact:', 'share on', 'send this', 'whatsapp', 'copy link',
    'advertisement', 'sponsored', 'promo code', 'follow pulse',
    'follow bellanaija', 'legit.ng reported', 'also reported',
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


def fetch_rss(url, verify=True):
    try:
        res = requests.get(url, headers=HEADERS, timeout=20, verify=verify)
        if res.status_code != 200:
            log.warning(f'RSS fetch failed {res.status_code}: {url}')
            return None
        return res.text
    except requests.exceptions.SSLError:
        if verify:
            log.warning(f'SSL error for {url} — retrying with verify=False')
            return fetch_rss(url, verify=False)
        log.error(f'SSL error (verify=False also failed): {url}')
        return None
    except requests.exceptions.Timeout:
        log.warning(f'Timeout fetching RSS: {url}')
        return None
    except Exception as e:
        log.error(f'RSS fetch error {url}: {e}')
        return None


def fetch_full_content(url, verify=True):
    """Fetch full article and return (clean_content, image_url)."""
    try:
        res = requests.get(url, headers=HEADERS, timeout=20, verify=verify)
        if res.status_code != 200:
            return None, None

        soup = BeautifulSoup(res.text, 'lxml')

        image_url = None
        og_img = soup.find('meta', property='og:image')
        if og_img and og_img.get('content', '').startswith('http'):
            image_url = og_img['content']

        article = None
        for selector in [
            'article', '.post-body', '.entry-content', '.post-content',
            '.article-body', '.story-body', '.content-body', 'main',
        ]:
            article = soup.select_one(selector)
            if article:
                break

        if not article:
            return None, image_url

        for tag in article.find_all(JUNK_TAGS):
            tag.decompose()

        for el in article.find_all(class_=re.compile(
            r'share|social|subscribe|newsletter|related|comment|ad|widget|sidebar',
            re.IGNORECASE
        )):
            el.decompose()

        paragraphs = []
        for tag in article.find_all(['p', 'h2', 'h3', 'h4', 'blockquote', 'ul', 'ol']):
            text = tag.get_text(strip=True)
            if len(text) < 40:
                continue
            if any(kw in text.lower() for kw in ADULT_KEYWORDS):
                continue
            if any(phrase in text.lower() for phrase in JUNK_PHRASES):
                continue
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
        return (content if len(content) > 100 else None), image_url

    except requests.exceptions.SSLError:
        if verify:
            log.warning(f'SSL error fetching article {url} — retrying with verify=False')
            return fetch_full_content(url, verify=False)
        return None, None
    except requests.exceptions.Timeout:
        log.warning(f'Timeout fetching article: {url}')
        return None, None
    except Exception as e:
        log.error(f'Full content fetch error {url}: {e}')
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
    verify   = source.get('verify', True)

    log.info(f'── Crawling: {name}')
    xml = fetch_rss(rss_url, verify=verify)
    if not xml:
        return 0

    soup  = BeautifulSoup(xml, 'xml')
    items = soup.find_all('item')
    count = 0

    for item in items[:50]:
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

            content, page_image = fetch_full_content(url, verify=verify)
            image_url    = extract_image(item, raw_desc) or page_image
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
            time.sleep(0.5)

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

    # Keep only the latest 500 posts
    try:
        latest_ids = [
            r.id for r in BlogPost.query
            .order_by(BlogPost.published_at.desc())
            .limit(500).all()
        ]
        if latest_ids:
            BlogPost.query.filter(~BlogPost.id.in_(latest_ids)).delete(
                synchronize_session=False
            )
            db.session.commit()
            log.info('  Pruned old blog posts — keeping latest 500')
    except Exception as e:
        db.session.rollback()
        log.error(f'  Pruning error: {e}')

    log.info(f'═══ Blog crawl done: {total} new posts ═══')