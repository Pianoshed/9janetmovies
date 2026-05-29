from flask import Blueprint, jsonify, request
from app.models.blog_post import BlogPost
from app.extensions import db
from newspaper import Article

blog_bp = Blueprint('blog', __name__, url_prefix='/api')


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
        try:
            article = Article(post.source_url)
            article.download()
            article.parse()
            post.content = article.text
            db.session.commit()
            data['content'] = article.text
        except:
            data['content'] = post.summary  # fallback to summary

    return jsonify(data)