"""Reminder model for tracking reminder schedules and notification history"""
from datetime import datetime, timezone
from .tour import db


def utc_now():
    """Return current UTC time (timezone-aware)"""
    return datetime.now(timezone.utc)


class Reminder(db.Model):
    """Reminder model for storing reminder schedules and notification history"""
    __tablename__ = 'reminders'

    id = db.Column(db.Integer, primary_key=True)
    trip_schedule_id = db.Column(db.Integer, db.ForeignKey('trip_schedules.id'), nullable=False, index=True)
    reminder_type = db.Column(db.String(50), nullable=False)  # email, sms
    remind_at = db.Column(db.DateTime, nullable=False, index=True)
    message = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, sent, failed, cancelled
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relationship
    trip_schedule = db.relationship('TripSchedule', back_populates='reminders')

    def __repr__(self):
        return f'<Reminder {self.id} - Trip {self.trip_schedule_id}>'

    def to_dict(self):
        """Convert reminder object to dictionary"""
        return {
            'id': self.id,
            'trip_schedule_id': self.trip_schedule_id,
            'reminder_type': self.reminder_type,
            'remind_at': self.remind_at.isoformat() if self.remind_at else None,
            'message': self.message,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
