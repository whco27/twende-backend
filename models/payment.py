"""Payment model for tracking M-Pesa transactions"""
from datetime import datetime, timezone
from .tour import db


def utc_now():
    """Return current UTC time (timezone-aware)"""
    return datetime.now(timezone.utc)


class Payment(db.Model):
    """Payment model for storing M-Pesa payment information"""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, index=True)
    merchant_request_id = db.Column(db.String(100), index=True)
    checkout_request_id = db.Column(db.String(100), unique=True, index=True)
    mpesa_receipt_number = db.Column(db.String(50))
    transaction_date = db.Column(db.DateTime)
    phone_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='initiated')  # initiated, pending, completed, failed, cancelled
    result_code = db.Column(db.Integer)
    result_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relationship to Booking
    booking = db.relationship('Booking', backref=db.backref('payments', lazy=True))

    def __repr__(self):
        return f'<Payment {self.id} - Booking {self.booking_id}>'

    def to_dict(self):
        """Convert payment object to dictionary"""
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'merchant_request_id': self.merchant_request_id,
            'checkout_request_id': self.checkout_request_id,
            'mpesa_receipt_number': self.mpesa_receipt_number,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'phone_number': self.phone_number,
            'amount': self.amount,
            'status': self.status,
            'result_code': self.result_code,
            'result_description': self.result_description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
