from flask import Blueprint, make_response
from feedgen.feed import FeedGenerator
from app.models.movie import Movie
from app.models.series import Series
from datetime import timezone, datetime

rss_bp = Blueprint('rss', __name__, url_prefix='/api')

@rss_bp.route('/rss')
def rss_feed():
    fg = FeedGenerator()
    fg.id('https://9janetmovies.com.ng/')
    fg.title('9janetmovies - Free Movie Downloads')
    fg.link(href='https://9janetmovies.com.ng/', rel='alternate')
    fg.link(href='https://9janetmovies.com.ng/rss', rel='self')
    fg.description('Latest Nollywood, Hollywood, Korean and more movie downloads.')
    fg.language('en')

    movies = Movie.query.order_by(Movie.created_at.desc()).limit(50).all()
    series = Series.query.order_by(Series.created_at.desc()).limit(50).all()

    items = [('movie', m) for m in movies] + [('series', s) for s in series]

    items.sort(
        key=lambda x: x[1].created_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True
    )
    items = items[:50]

    for item_type, item in items:
        fe = fg.add_entry()

        if item_type == 'series':
            url = f'https://9janetmovies.com.ng/series/{item.slug}'
            title = f'{item.title} [Series]'
        else:
            url = f'https://9janetmovies.com.ng/movie/{item.slug}'
            title = f'{item.title} ({item.year})' if item.year else item.title

        fe.id(url)
        fe.title(title)
        fe.link(href=url)
        fe.category({'term': item.genre} if item.genre else {'term': item_type.capitalize()})

        description = item.description or f'Download {item.title} free on 9janetmovies.'
        if item.poster_url:
            description = f'<img src="{item.poster_url}" alt="{item.title}"/><br/>{description}'
        fe.description(description)

        if item.created_at:
            fe.pubDate(item.created_at.replace(tzinfo=timezone.utc))

    response = make_response(fg.rss_str(pretty=True))
    response.headers['Content-Type'] = 'application/rss+xml; charset=utf-8'
    return response