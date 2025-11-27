from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Tour(db.Model):
    """Tour model for storing tour information"""
    __tablename__ = 'tours'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500))
    available_slots = db.Column(db.Integer, default=10)
    
    def __repr__(self):
        return f'<Tour {self.title}>'
    
    def to_dict(self):
        """Convert tour object to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'duration': self.duration,
            'location': self.location,
            'image_url': self.image_url,
            'available_slots': self.available_slots
        }
