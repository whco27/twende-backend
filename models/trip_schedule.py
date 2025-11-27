"""TripSchedule model for tracking travel dates, locations, and statuses"""
from datetime import datetime, timezone
from .tour import db


def utc_now():
    """Return current UTC time (timezone-aware)"""
    return datetime.now(timezone.utc)


class TripSchedule(db.Model):
    """TripSchedule model for storing trip schedule information"""
    __tablename__ = 'trip_schedules'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200), nullable=False)
    departure_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='scheduled')  # scheduled, in_progress, completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = db.relationship('User', backref=db.backref('trip_schedules', lazy=True))
    booking = db.relationship('Booking', backref=db.backref('trip_schedule', uselist=False))
    reminders = db.relationship('Reminder', back_populates='trip_schedule', lazy=True,
                                cascade='all, delete-orphan')

    def __repr__(self):
        return f'<TripSchedule {self.id} - {self.title}>'

    def to_dict(self):
        """Convert trip schedule object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'booking_id': self.booking_id,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'departure_date': self.departure_date.isoformat() if self.departure_date else None,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'reminders': [r.to_dict() for r in self.reminders] if self.reminders else []
        }
