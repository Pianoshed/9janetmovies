from flask import Blueprint, make_response
from feedgen.feed import FeedGenerator
from app.models.movie import Movie
from datetime import timezone

rss_bp = Blueprint('rss', __name__)

@rss_bp.route('/rss')
def rss_feed():
    fg = FeedGenerator()
    fg.id('https://9janetmovies.com.ng/')
    fg.title('9janetmovies – Free Movie Downloads')
    fg.link(href='https://9janetmovies.com.ng/', rel='alternate')
    fg.link(href='https://9janetmovies.com.ng/rss', rel='self')
    fg.description('Latest Nollywood, Hollywood, Korean & more movie downloads.')
    fg.language('en')

    movies = Movie.query.order_by(Movie.created_at.desc()).limit(50).all()

    for movie in movies:
        fe = fg.add_entry()
        fe.id(f'https://9janetmovies.com.ng/movie/{movie.slug}')
        fe.title(f'{movie.title} ({movie.year})' if movie.year else movie.title)
        fe.link(href=f'https://9janetmovies.com.ng/movie/{movie.slug}')
        fe.category({'term': movie.genre} if movie.genre else {'term': 'Movie'})

        description = movie.description or f'Download {movie.title} free on 9janetmovies.'
        if movie.poster_url:
            description = f'<img src="{movie.poster_url}" alt="{movie.title}"/><br/>{description}'
        fe.description(description)

        if movie.created_at:
            fe.pubDate(movie.created_at.replace(tzinfo=timezone.utc))

    response = make_response(fg.rss_str(pretty=True))
    response.headers['Content-Type'] = 'application/rss+xml; charset=utf-8'
    return response