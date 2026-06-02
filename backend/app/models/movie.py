from app import db
from datetime import datetime

class Movie(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    slug        = db.Column(db.String(220), unique=True, nullable=False)
    poster_url  = db.Column(db.String(500))
    year        = db.Column(db.Integer)
    genre       = db.Column(db.String(100))
    description = db.Column(db.Text)
    is_trending = db.Column(db.Boolean, default=False)
    badge       = db.Column(db.String(20), default='New')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    links       = db.relationship('DownloadLink', backref='movie', lazy=True)

    @property
    def download_links(self):
        return self.links

    def to_dict(self):
        return {
            'id':          self.id,
            'title':       self.title,
            'slug':        self.slug,
            'poster_url':  self.poster_url,
            'year':        self.year,
            'genre':       self.genre,
            'description': self.description,
            'is_trending': self.is_trending,
            'badge':       self.badge,
            'created_at':  self.created_at.isoformat(),
            'links':       [l.to_dict() for l in self.links]
        }