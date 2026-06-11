from app import db
from datetime import datetime

class Series(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    slug        = db.Column(db.String(220), unique=True, nullable=False)
    poster_url  = db.Column(db.String(500))
    genre       = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    episodes    = db.relationship('Episode', backref='series', lazy=True)

    def to_dict(self, slim=False):
        data = {
            'id':          self.id,
            'title':       self.title,
            'slug':        self.slug,
            'poster_url':  self.poster_url,
            'genre':       self.genre,
            'description': self.description,
            'created_at':  self.created_at.isoformat(),
        }
        if not slim:
            data['episodes'] = [e.to_dict() for e in self.episodes]
        return data