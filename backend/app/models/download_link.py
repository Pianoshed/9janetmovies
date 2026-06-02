from app import db

class DownloadLink(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    label    = db.Column(db.String(50))
    url      = db.Column(db.String(1000))
    host     = db.Column(db.String(100))

    def to_dict(self):
        return {
            'label': self.label,
            'url':   self.url,
            'host':  self.host
        }