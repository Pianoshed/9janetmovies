from app import db

class DownloadLink(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    label    = db.Column(db.String(50))    # "480p", "720p", "1080p"
    url      = db.Column(db.String(1000))  # GDrive, Mediafire etc
    host     = db.Column(db.String(100))   # "GDrive", "Mediafire"

    def to_dict(self):
        return {
            'label': self.label,
            'url':   self.url,
            'host':  self.host
        }