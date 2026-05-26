from app import db

class Episode(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    series_id  = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=False)
    season     = db.Column(db.Integer, default=1)
    episode    = db.Column(db.Integer)
    title      = db.Column(db.String(200))
    url        = db.Column(db.String(1000))  # external link
    host       = db.Column(db.String(100))

    def to_dict(self):
        return {
            'season':  self.season,
            'episode': self.episode,
            'title':   self.title,
            'url':     self.url,
            'host':    self.host
        }