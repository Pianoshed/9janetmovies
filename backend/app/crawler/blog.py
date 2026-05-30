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

# ── All sources below are free, publicly available RSS feeds ──────────────────

SOURCES = [
    # ── Fitness & Exercise ────────────────────────────────────────────────
    {
        'name':     'Nerd Fitness',
        'rss':      'https://www.nerdfitness.com/blog/feed/',
        'category': 'Fitness',
        'verify':   True,
    },
    {
        'name':     'Breaking Muscle',
        'rss':      'https://breakingmuscle.com/feed/',
        'category': 'Fitness',
        'verify':   True,
    },
    {
        'name':     'Girls Gone Strong',
        'rss':      'https://www.girlsgonestrong.com/blog/feed/',
        'category': 'Fitness',
        'verify':   True,
    },
    {
        'name':     'BarBend',
        'rss':      'https://barbend.com/feed/',
        'category': 'Fitness',
        'verify':   True,
    },

    # ── Nutrition & Diet ─────────────────────────────────────────────────
    {
        'name':     'Precision Nutrition',
        'rss':      'https://www.precisionnutrition.com/feed',
        'category': 'Nutrition',
        'verify':   True,
    },
    {
        'name':     'Healthline Nutrition',
        'rss':      'https://www.healthline.com/rss/nutrition',
        'category': 'Nutrition',
        'verify':   True,
    },
    {
        'name':     'Examine.com',
        'rss':      'https://examine.com/feed/',
        'category': 'Nutrition',
        'verify':   True,
    },
    {
        'name':     'Nom Nom Paleo',
        'rss':      'https://nomnompaleo.com/feed',
        'category': 'Nutrition',
        'verify':   True,
    },

    # ── Mental Wellness & Mindfulness ─────────────────────────────────────
    {
        'name':     'Mindful',
        'rss':      'https://www.mindful.org/feed/',
        'category': 'Mental Wellness',
        'verify':   True,
    },
    {
        'name':     'Psychology Today Wellness',
        'rss':      'https://www.psychologytoday.com/us/front/feed',
        'category': 'Mental Wellness',
        'verify':   True,
    },
    {
        'name':     'Greater Good Science Center',
        'rss':      'https://greatergood.berkeley.edu/feeds/all-articles.xml',
        'category': 'Mental Wellness',
        'verify':   True,
    },

    # ── Healthy Living & Lifestyle ────────────────────────────────────────
    {
        'name':     'Well+Good',
        'rss':      'https://www.wellandgood.com/feed/',
        'category': 'Lifestyle',
        'verify':   True,
    },
    {
        'name':     'MindBodyGreen',
        'rss':      'https://www.mindbodygreen.com/rss.xml',
        'category': 'Lifestyle',
        'verify':   True,
    },
    {
        'name':     'Healthline',
        'rss':      'https://www.healthline.com/rss/health-news',
        'category': 'Lifestyle',
        'verify':   True,
    },
    {
        'name':     'Medical News Today',
        'rss':      'https://www.medicalnewstoday.com/rss',
        'category': 'Lifestyle',
        'verify':   True,
    },

    # ── Weight Loss & Body Transformation ────────────────────────────────
    {
        'name':     'Obesity Help',
        'rss':      'https://www.obesityhelp.com/articles/rss/',
        'category': 'Weight Loss',
        'verify':   True,
    },
    {
        'name':     'Lose It! Blog',
        'rss':      'https://blog.loseit.com/feed/',
        'category': 'Weight Loss',
        'verify':   True,
    },

    # ── Sleep & Recovery ─────────────────────────────────────────────────
    {
        'name':     'Sleep Foundation',
        'rss':      'https://www.sleepfoundation.org/feed',
        'category': 'Recovery',
        'verify':   True,
    },

    # ── YouTube Channels (via RSS — no API key needed) ────────────────────
    # YouTube exposes free, public RSS feeds for every channel.
    # Format: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
    {
        'name':     'Jeff Nippard (YouTube)',
        'rss':      'https://www.youtube.com/feeds/videos.xml?channel_id=UC68TLK0mAEzUyHx5x5k-S1Q',
        'category': 'Fitness',
        'verify':   True,
    },
    {
        'name':     'Athlean-X (YouTube)',
        'rss':      'https://www.youtube.com/feeds/videos.xml?channel_id=UCe0TLA0EsQbE-MjuHXevran',
        'category': 'Fitness',
        'verify':   True,
    },
    {
        'name':     'Doctor Mike (YouTube)',
        'rss':      'https://www.youtube.com/feeds/videos.xml?channel_id=UC0QHWhjbe5fGJEPz3sZqH6A',
        'category': 'Lifestyle',
        'verify':   True,
    },
    {
        'name':     'Thomas DeLauer – Nutrition (YouTube)',
        'rss':      'https://www.youtube.com/feeds/videos.xml?channel_id=UC70SrI3VkT1MXALRtf0pcHg',
        'category': 'Nutrition',
        'verify':   True,
    },
    {
        'name':     'Yoga With Adriene (YouTube)',
        'rss':      'https://www.youtube.com/feeds/videos.xml?channel_id=UCFKE7WVJfvaHW5q283SxchA',
        'category': 'Mental Wellness',
        'verify':   True,
    },
    {
        'name':     'Autumn Bates – Nutrition (YouTube)',
        'rss':      'https://www.youtube.com/feeds/videos.xml?channel_id=UCnLRo9llNnMiRRIxqm3F0Eg',
        'category': 'Nutrition',
        'verify':   True,
    },
    {
        'name':     'Chloe Ting – Fitness (YouTube)',
        'rss':      'https://www.youtube.com/feeds/videos.xml?channel_id=UCCgLoMYIyP0U56dEhEL1wXQ',
        'category': 'Fitness',
        'verify':   True,
    },
    {
        'name':     'Bob & Brad – Physical Therapy (YouTube)',
        'rss':      'https://www.youtube.com/feeds/videos.xml?channel_id=UCmTe0LsfEbpkDpgrxKAWbRA',
        'category': 'Recovery',
        'verify':   True,
    },
]

RELEVANT_KEYWORDS = [
    # Fitness
    'workout', 'exercise', 'training', 'gym', 'muscle', 'strength',
    'cardio', 'hiit', 'yoga', 'pilates', 'stretching', 'flexibility',
    'running', 'cycling', 'swimming', 'crossfit', 'bodybuilding',
    # Nutrition
    'nutrition', 'diet', 'protein', 'calories', 'carbs', 'fat', 'fibre',
    'meal', 'recipe', 'eat', 'food', 'supplement', 'vitamin', 'mineral',
    'intermittent fasting', 'keto', 'paleo', 'vegan', 'plant-based',
    # Health
    'health', 'wellness', 'weight loss', 'fat loss', 'metabolism',
    'blood pressure', 'heart', 'immune', 'inflammation', 'gut',
    'sleep', 'recovery', 'rest', 'hydration', 'water',
    # Mental
    'mental health', 'mindfulness', 'meditation', 'stress', 'anxiety',
    'mood', 'depression', 'therapy', 'self-care', 'habit', 'motivation',
    # Lifestyle
    'lifestyle', 'healthy living', 'body', 'transformation', 'challenge',
    'tip', 'guide', 'routine', 'plan',
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
    'read also', 'follow us', 'subscribe', 'newsletter', 'click here',
    'source:', 'tags:', 'contact:', 'share on', 'send this',
    'whatsapp', 'copy link', 'advertisement', 'sponsored', 'promo code',
    'sign up', 'buy now', 'shop now', 'limited offer', 'discount',
]


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def extract_youtube_thumbnail(item_soup):
    """Extract YouTube video thumbnail from the RSS feed's media group."""
    thumb = item_soup.find('media:thumbnail')
    if thumb and thumb.get('url', '').startswith('http'):
        return thumb['url']
    # Fallback: build from video ID
    video_id_tag = item_soup.find('yt:videoId')
    if video_id_tag:
        vid = video_id_tag.get_text(strip=True)
        return f'https://img.youtube.com/vi/{vid}/hqdefault.jpg'
    return None


def extract_youtube_content(item_soup):
    """Build an embeddable iframe block for YouTube entries."""
    video_id_tag = item_soup.find('yt:videoId')
    if not video_id_tag:
        return None
    vid = video_id_tag.get_text(strip=True)

    description = ''
    media_desc = item_soup.find('media:description')
    if media_desc:
        raw = media_desc.get_text(strip=True)[:1200]
        description = f'<p>{raw}</p>' if raw else ''

    embed = (
        f'<div class="video-embed" style="position:relative;padding-top:56.25%;margin-bottom:1rem;">'
        f'<iframe src="https://www.youtube.com/embed/{vid}" '
        f'frameborder="0" allowfullscreen '
        f'style="position:absolute;top:0;left:0;width:100%;height:100%;"></iframe>'
        f'</div>'
    )
    return embed + description


def is_youtube_source(rss_url):
    return 'youtube.com/feeds/videos.xml' in rss_url


def parse_date(item_soup):
    for tag_name in ['pubDate', 'published', 'updated']:
        tag = item_soup.find(tag_name)
        if tag:
            try:
                return parsedate_to_datetime(tag.text.strip()).replace(tzinfo=None)
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
    youtube  = is_youtube_source(rss_url)

    log.info(f'── Crawling: {name}')
    xml = fetch_rss(rss_url, verify=verify)
    if not xml:
        return 0

    soup  = BeautifulSoup(xml, 'xml')
    # YouTube Atom feeds use <entry>, standard RSS uses <item>
    items = soup.find_all('entry') if youtube else soup.find_all('item')
    count = 0

    for item in items[:50]:
        try:
            title_tag = item.find('title')
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)

            # Link extraction differs between Atom (YouTube) and RSS
            if youtube:
                link_tag = item.find('link')
                url = link_tag.get('href', '').strip() if link_tag else ''
            else:
                link_tag = item.find('link')
                url = link_tag.get_text(strip=True) if link_tag else ''

            if not title or not url:
                continue

            # Summary / description
            if youtube:
                media_desc = item.find('media:description')
                raw_desc   = media_desc.get_text(strip=True) if media_desc else ''
            else:
                desc_tag = item.find('description') or item.find('content:encoded')
                raw_desc = desc_tag.get_text(strip=True) if desc_tag else ''

            summary = BeautifulSoup(raw_desc, 'lxml').get_text(separator=' ')[:600].strip()

            if not is_relevant(title, summary):
                continue

            # Content + image
            if youtube:
                content   = extract_youtube_content(item)
                image_url = extract_youtube_thumbnail(item)
            else:
                content, page_image = fetch_full_content(url, verify=verify)
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
            time.sleep(0.3 if youtube else 0.5)

        except Exception as e:
            log.error(f'  Error processing item from {name}: {e}')
            continue

    return count


def run_blog_crawl():
    log.info('═══ Health & Fitness blog crawl started ═══')
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
            log.info('  Pruned old posts — keeping latest 500')
    except Exception as e:
        db.session.rollback()
        log.error(f'  Pruning error: {e}')

    log.info(f'═══ Health & Fitness crawl done: {total} new posts ═══')