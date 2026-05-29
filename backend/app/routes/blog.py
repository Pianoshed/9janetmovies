from flask import Blueprint, jsonify, request
from app.models.blog_post import BlogPost
from app import db
import requests
from bs4 import BeautifulSoup

blog_bp = Blueprint('blog', __name__, url_prefix='/api')


def scrape_article_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Remove junk
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()
        
        # Try common article containers
        article = (
            soup.find('article') or
            soup.find(class_='article-body') or
            soup.find(class_='post-content') or
            soup.find(class_='entry-content') or
            soup.find('main')
        )
        
        if article:
            return article.get_text(separator='\n', strip=True)
        return None
    except Exception:
        return None


@blog_bp.route('/blog')
def get_posts():
    page     = request.args.get('page', 1, type=int)
    category = request.args.get('category', None)
    limit    = request.args.get('limit', 10, type=int)

    query = BlogPost.query

    if category:
        query = query.filter(BlogPost.category.ilike(f'%{category}%'))

    posts = query.order_by(BlogPost.published_at.desc()).paginate(
        page=page, per_page=min(limit, 20), error_out=False
    )

    return jsonify({
        'posts':   [p.to_dict() for p in posts.items],
        'total':   posts.total,
        'pages':   posts.pages,
        'current': posts.page,
    })


@blog_bp.route('/blog/<slug>')
def get_post(slug):
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    data = post.to_dict()

    if not post.content and post.source_url:
        content = scrape_article_content(post.source_url)
        if content:
            post.content = content
            db.session.commit()
        data['content'] = content or post.summary

    return jsonify(data)