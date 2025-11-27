"""Booking routes for tour reservations"""
from flask import Blueprint, jsonify, request
from models import db, Booking, Tour, User
from datetime import datetime
from werkzeug.exceptions import NotFound

bookings_bp = Blueprint('bookings', __name__, url_prefix='/api/bookings')


@bookings_bp.route('/', methods=['GET'])
def get_bookings():
    """Get all bookings (optionally filtered by user_id)"""
    try:
        user_id = request.args.get('user_id', type=int)
        status = request.args.get('status')

        query = Booking.query

        if user_id:
            query = query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)

        bookings = query.order_by(Booking.created_at.desc()).all()

        return jsonify({
            'success': True,
            'bookings': [booking.to_dict() for booking in bookings]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bookings_bp.route('/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Get a specific booking by ID"""
    try:
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return jsonify({
                'success': False,
                'error': 'Booking not found'
            }), 404

        return jsonify({
            'success': True,
            'booking': booking.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bookings_bp.route('/', methods=['POST'])
def create_booking():
    """Create a new booking"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate required fields
        required_fields = ['user_id', 'tour_id', 'tour_date', 'number_of_guests']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Verify user exists
        user = db.session.get(User, data['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Verify tour exists and has available slots
        tour = db.session.get(Tour, data['tour_id'])
        if not tour:
            return jsonify({
                'success': False,
                'error': 'Tour not found'
            }), 404

        # Validate number_of_guests
        try:
            number_of_guests = int(data['number_of_guests'])
            if number_of_guests < 1:
                return jsonify({
                    'success': False,
                    'error': 'Number of guests must be at least 1'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid number_of_guests value'
            }), 400

        if tour.available_slots < number_of_guests:
            return jsonify({
                'success': False,
                'error': f'Not enough available slots. Only {tour.available_slots} slots remaining'
            }), 400

        # Parse tour date
        try:
            tour_date = datetime.strptime(data['tour_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid tour_date format. Use YYYY-MM-DD'
            }), 400

        # Calculate total amount
        total_amount = tour.price * number_of_guests

        # Create booking
        new_booking = Booking(
            user_id=data['user_id'],
            tour_id=data['tour_id'],
            tour_date=tour_date,
            number_of_guests=number_of_guests,
            total_amount=total_amount,
            notes=data.get('notes')
        )

        # Reserve slots (will be confirmed after payment)
        tour.available_slots -= number_of_guests

        db.session.add(new_booking)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Booking created successfully',
            'booking': new_booking.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bookings_bp.route('/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    """Update booking status"""
    try:
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return jsonify({
                'success': False,
                'error': 'Booking not found'
            }), 404

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Update allowed fields
        if 'status' in data:
            booking.status = data['status']
        if 'payment_status' in data:
            booking.payment_status = data['payment_status']
        if 'payment_reference' in data:
            booking.payment_reference = data['payment_reference']
        if 'notes' in data:
            booking.notes = data['notes']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Booking updated successfully',
            'booking': booking.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bookings_bp.route('/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    """Cancel a booking"""
    try:
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return jsonify({
                'success': False,
                'error': 'Booking not found'
            }), 404

        if booking.status == 'cancelled':
            return jsonify({
                'success': False,
                'error': 'Booking is already cancelled'
            }), 400

        if booking.status == 'completed':
            return jsonify({
                'success': False,
                'error': 'Cannot cancel a completed booking'
            }), 400

        # Restore available slots
        tour = db.session.get(Tour, booking.tour_id)
        if tour:
            tour.available_slots += booking.number_of_guests

        booking.status = 'cancelled'
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Booking cancelled successfully',
            'booking': booking.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bookings_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_bookings(user_id):
    """Get all bookings for a specific user"""
    try:
        # Verify user exists
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all()

        return jsonify({
            'success': True,
            'bookings': [booking.to_dict() for booking in bookings]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
