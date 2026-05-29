from app import db
from datetime import datetime


class BlogPost(db.Model):
    __tablename__ = 'blog_post'

    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(300), nullable=False)
    slug         = db.Column(db.String(320), unique=True, nullable=False)
    summary      = db.Column(db.Text)
    image_url    = db.Column(db.String(500))
    source_name  = db.Column(db.String(100))
    source_url   = db.Column(db.String(500))
    category     = db.Column(db.String(50))
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':           self.id,
            'title':        self.title,
            'slug':         self.slug,
            'summary':      self.summary,
            'image_url':    self.image_url,
            'source_name':  self.source_name,
            'source_url':   self.source_url,
            'category':     self.category,
            'published_at': self.published_at.isoformat(),
            'created_at':   self.created_at.isoformat(),
        }