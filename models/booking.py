"""Booking model for tour reservations"""
from datetime import datetime, timezone
from .tour import db


def utc_now():
    """Return current UTC time (timezone-aware)"""
    return datetime.now(timezone.utc)


class Booking(db.Model):
    """Booking model for storing tour bookings"""
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tour_id = db.Column(db.Integer, db.ForeignKey('tours.id'), nullable=False, index=True)
    booking_date = db.Column(db.DateTime, default=utc_now)
    tour_date = db.Column(db.Date, nullable=False)
    number_of_guests = db.Column(db.Integer, nullable=False, default=1)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, cancelled, completed
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed, refunded
    payment_reference = db.Column(db.String(100))  # M-Pesa transaction reference
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relationship to Tour
    tour = db.relationship('Tour', backref=db.backref('bookings', lazy=True))

    def __repr__(self):
        return f'<Booking {self.id} - User {self.user_id} Tour {self.tour_id}>'

    def to_dict(self):
        """Convert booking object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'tour_id': self.tour_id,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'tour_date': self.tour_date.isoformat() if self.tour_date else None,
            'number_of_guests': self.number_of_guests,
            'total_amount': self.total_amount,
            'status': self.status,
            'payment_status': self.payment_status,
            'payment_reference': self.payment_reference,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'tour': self.tour.to_dict() if self.tour else None
        }
