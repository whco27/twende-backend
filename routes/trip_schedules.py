"""Trip schedule routes for managing trip schedules and reminders"""
from flask import Blueprint, jsonify, request
from models import db, TripSchedule, Reminder, User, Booking
from datetime import datetime, timezone
from services.notifications import notification_service
import logging

logger = logging.getLogger(__name__)

trip_schedules_bp = Blueprint('trip_schedules', __name__, url_prefix='/api/trip-schedules')

# Default pagination settings
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def parse_datetime(date_str):
    """Parse datetime string in ISO format"""
    if not date_str:
        return None
    try:
        # Handle both with and without microseconds
        if 'T' in date_str:
            # ISO format with time
            if '.' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            # Date only format
            return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None


@trip_schedules_bp.route('/', methods=['GET'])
def get_trip_schedules():
    """Get all trip schedules with optional filtering and pagination"""
    try:
        user_id = request.args.get('user_id', type=int)
        status = request.args.get('status')
        page = request.args.get('page', DEFAULT_PAGE, type=int)
        per_page = request.args.get('per_page', DEFAULT_PER_PAGE, type=int)

        # Validate pagination parameters
        if page < 1:
            page = DEFAULT_PAGE
        if per_page < 1 or per_page > MAX_PER_PAGE:
            per_page = DEFAULT_PER_PAGE

        query = TripSchedule.query

        if user_id:
            query = query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)

        # Order by departure date
        pagination = query.order_by(TripSchedule.departure_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'success': True,
            'trip_schedules': [ts.to_dict() for ts in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting trip schedules: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_schedules_bp.route('/<int:schedule_id>', methods=['GET'])
def get_trip_schedule(schedule_id):
    """Get a specific trip schedule by ID"""
    try:
        trip_schedule = db.session.get(TripSchedule, schedule_id)
        if not trip_schedule:
            return jsonify({
                'success': False,
                'error': 'Trip schedule not found'
            }), 404

        return jsonify({
            'success': True,
            'trip_schedule': trip_schedule.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Error getting trip schedule: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_schedules_bp.route('/', methods=['POST'])
def create_trip_schedule():
    """Create a new trip schedule"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate required fields
        required_fields = ['user_id', 'title', 'location', 'departure_date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Validate that string fields are not empty
        string_fields = ['title', 'location']
        for field in string_fields:
            if not data[field] or not str(data[field]).strip():
                return jsonify({
                    'success': False,
                    'error': f'{field} cannot be empty'
                }), 400

        # Verify user exists
        user = db.session.get(User, data['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Verify booking exists if provided
        if data.get('booking_id'):
            booking = db.session.get(Booking, data['booking_id'])
            if not booking:
                return jsonify({
                    'success': False,
                    'error': 'Booking not found'
                }), 404

        # Parse dates
        departure_date = parse_datetime(data['departure_date'])
        if not departure_date:
            return jsonify({
                'success': False,
                'error': 'Invalid departure_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
            }), 400

        return_date = None
        if data.get('return_date'):
            return_date = parse_datetime(data['return_date'])
            if not return_date:
                return jsonify({
                    'success': False,
                    'error': 'Invalid return_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                }), 400

        # Create trip schedule
        new_trip_schedule = TripSchedule(
            user_id=data['user_id'],
            booking_id=data.get('booking_id'),
            title=data['title'].strip(),
            description=data.get('description'),
            location=data['location'].strip(),
            departure_date=departure_date,
            return_date=return_date,
            status=data.get('status', 'scheduled'),
            notes=data.get('notes')
        )

        db.session.add(new_trip_schedule)
        db.session.commit()

        logger.info(f"Trip schedule created: id={new_trip_schedule.id}")

        return jsonify({
            'success': True,
            'message': 'Trip schedule created successfully',
            'trip_schedule': new_trip_schedule.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating trip schedule: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_schedules_bp.route('/<int:schedule_id>', methods=['PUT'])
def update_trip_schedule(schedule_id):
    """Update an existing trip schedule"""
    try:
        trip_schedule = db.session.get(TripSchedule, schedule_id)
        if not trip_schedule:
            return jsonify({
                'success': False,
                'error': 'Trip schedule not found'
            }), 404

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate string fields if provided
        string_fields = ['title', 'location']
        for field in string_fields:
            if field in data and (not data[field] or not str(data[field]).strip()):
                return jsonify({
                    'success': False,
                    'error': f'{field} cannot be empty'
                }), 400

        # Update fields if provided
        if 'title' in data:
            trip_schedule.title = data['title'].strip()
        if 'description' in data:
            trip_schedule.description = data['description']
        if 'location' in data:
            trip_schedule.location = data['location'].strip()
        if 'departure_date' in data:
            departure_date = parse_datetime(data['departure_date'])
            if not departure_date:
                return jsonify({
                    'success': False,
                    'error': 'Invalid departure_date format'
                }), 400
            trip_schedule.departure_date = departure_date
        if 'return_date' in data:
            if data['return_date']:
                return_date = parse_datetime(data['return_date'])
                if not return_date:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid return_date format'
                    }), 400
                trip_schedule.return_date = return_date
            else:
                trip_schedule.return_date = None
        if 'status' in data:
            trip_schedule.status = data['status']
        if 'notes' in data:
            trip_schedule.notes = data['notes']

        db.session.commit()

        logger.info(f"Trip schedule updated: id={schedule_id}")

        return jsonify({
            'success': True,
            'message': 'Trip schedule updated successfully',
            'trip_schedule': trip_schedule.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating trip schedule: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_schedules_bp.route('/<int:schedule_id>', methods=['DELETE'])
def delete_trip_schedule(schedule_id):
    """Delete a trip schedule"""
    try:
        trip_schedule = db.session.get(TripSchedule, schedule_id)
        if not trip_schedule:
            return jsonify({
                'success': False,
                'error': 'Trip schedule not found'
            }), 404

        db.session.delete(trip_schedule)
        db.session.commit()

        logger.info(f"Trip schedule deleted: id={schedule_id}")

        return jsonify({
            'success': True,
            'message': 'Trip schedule deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting trip schedule: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_schedules_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_trip_schedules(user_id):
    """Get all trip schedules for a specific user"""
    try:
        page = request.args.get('page', DEFAULT_PAGE, type=int)
        per_page = request.args.get('per_page', DEFAULT_PER_PAGE, type=int)

        # Validate pagination parameters
        if page < 1:
            page = DEFAULT_PAGE
        if per_page < 1 or per_page > MAX_PER_PAGE:
            per_page = DEFAULT_PER_PAGE

        # Verify user exists
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        pagination = TripSchedule.query.filter_by(user_id=user_id).order_by(
            TripSchedule.departure_date.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'trip_schedules': [ts.to_dict() for ts in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting user trip schedules: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Reminder routes

@trip_schedules_bp.route('/<int:schedule_id>/reminders', methods=['GET'])
def get_reminders(schedule_id):
    """Get all reminders for a trip schedule"""
    try:
        trip_schedule = db.session.get(TripSchedule, schedule_id)
        if not trip_schedule:
            return jsonify({
                'success': False,
                'error': 'Trip schedule not found'
            }), 404

        reminders = Reminder.query.filter_by(trip_schedule_id=schedule_id).order_by(
            Reminder.remind_at.asc()
        ).all()

        return jsonify({
            'success': True,
            'reminders': [r.to_dict() for r in reminders]
        }), 200

    except Exception as e:
        logger.error(f"Error getting reminders: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_schedules_bp.route('/<int:schedule_id>/reminders', methods=['POST'])
def create_reminder(schedule_id):
    """Create a new reminder for a trip schedule"""
    try:
        trip_schedule = db.session.get(TripSchedule, schedule_id)
        if not trip_schedule:
            return jsonify({
                'success': False,
                'error': 'Trip schedule not found'
            }), 404

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate required fields
        required_fields = ['reminder_type', 'remind_at']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Validate reminder_type
        valid_types = ['email', 'sms']
        if data['reminder_type'] not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid reminder_type. Must be one of: {", ".join(valid_types)}'
            }), 400

        # Parse remind_at datetime
        remind_at = parse_datetime(data['remind_at'])
        if not remind_at:
            return jsonify({
                'success': False,
                'error': 'Invalid remind_at format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
            }), 400

        # Create reminder
        new_reminder = Reminder(
            trip_schedule_id=schedule_id,
            reminder_type=data['reminder_type'],
            remind_at=remind_at,
            message=data.get('message'),
            status='pending'
        )

        db.session.add(new_reminder)
        db.session.commit()

        logger.info(f"Reminder created: id={new_reminder.id} for trip_schedule_id={schedule_id}")

        return jsonify({
            'success': True,
            'message': 'Reminder created successfully',
            'reminder': new_reminder.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating reminder: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_schedules_bp.route('/reminders/<int:reminder_id>', methods=['GET'])
def get_reminder(reminder_id):
    """Get a specific reminder by ID"""
    try:
        reminder = db.session.get(Reminder, reminder_id)
        if not reminder:
            return jsonify({
                'success': False,
                'error': 'Reminder not found'
            }), 404

        return jsonify({
            'success': True,
            'reminder': reminder.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Error getting reminder: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_schedules_bp.route('/reminders/<int:reminder_id>', methods=['PUT'])
def update_reminder(reminder_id):
    """Update a reminder"""
    try:
        reminder = db.session.get(Reminder, reminder_id)
        if not reminder:
            return jsonify({
                'success': False,
                'error': 'Reminder not found'
            }), 404

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Update fields if provided
        if 'reminder_type' in data:
            valid_types = ['email', 'sms']
            if data['reminder_type'] not in valid_types:
                return jsonify({
                    'success': False,
                    'error': f'Invalid reminder_type. Must be one of: {", ".join(valid_types)}'
                }), 400
            reminder.reminder_type = data['reminder_type']
        if 'remind_at' in data:
            remind_at = parse_datetime(data['remind_at'])
            if not remind_at:
                return jsonify({
                    'success': False,
                    'error': 'Invalid remind_at format'
                }), 400
            reminder.remind_at = remind_at
        if 'message' in data:
            reminder.message = data['message']
        if 'status' in data:
            reminder.status = data['status']

        db.session.commit()

        logger.info(f"Reminder updated: id={reminder_id}")

        return jsonify({
            'success': True,
            'message': 'Reminder updated successfully',
            'reminder': reminder.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating reminder: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_schedules_bp.route('/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    """Delete a reminder"""
    try:
        reminder = db.session.get(Reminder, reminder_id)
        if not reminder:
            return jsonify({
                'success': False,
                'error': 'Reminder not found'
            }), 404

        db.session.delete(reminder)
        db.session.commit()

        logger.info(f"Reminder deleted: id={reminder_id}")

        return jsonify({
            'success': True,
            'message': 'Reminder deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting reminder: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_schedules_bp.route('/reminders/pending', methods=['GET'])
def get_pending_reminders():
    """Get all pending reminders that are due to be sent"""
    try:
        now = datetime.now(timezone.utc)
        reminders = Reminder.query.filter(
            Reminder.status == 'pending',
            Reminder.remind_at <= now
        ).order_by(Reminder.remind_at.asc()).all()

        return jsonify({
            'success': True,
            'reminders': [r.to_dict() for r in reminders],
            'count': len(reminders)
        }), 200

    except Exception as e:
        logger.error(f"Error getting pending reminders: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_schedules_bp.route('/reminders/<int:reminder_id>/send', methods=['POST'])
def send_reminder(reminder_id):
    """Send a specific reminder notification"""
    try:
        reminder = db.session.get(Reminder, reminder_id)
        if not reminder:
            return jsonify({
                'success': False,
                'error': 'Reminder not found'
            }), 404

        if reminder.status == 'sent':
            return jsonify({
                'success': False,
                'error': 'Reminder has already been sent'
            }), 400

        if reminder.status == 'cancelled':
            return jsonify({
                'success': False,
                'error': 'Reminder has been cancelled'
            }), 400

        # Get trip schedule and user info
        trip_schedule = db.session.get(TripSchedule, reminder.trip_schedule_id)
        if not trip_schedule:
            return jsonify({
                'success': False,
                'error': 'Trip schedule not found'
            }), 404

        user = db.session.get(User, trip_schedule.user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Attempt to send notification
        sent = False
        error_message = None

        if reminder.reminder_type == 'email':
            # Use notification service to send email reminder
            sent = notification_service.send_trip_reminder_email(user, trip_schedule, reminder)
            if not sent:
                error_message = 'Failed to send email notification'
        elif reminder.reminder_type == 'sms':
            # TODO: Integrate with SMS provider (e.g., Twilio, Africa's Talking)
            # For now, we log the intent. SMS functionality requires additional
            # configuration and provider credentials.
            if user.phone_number:
                logger.info(f"SMS reminder would be sent to {user.phone_number}")
                # Mark as sent in development. In production, implement actual SMS.
                sent = True
            else:
                error_message = 'User does not have a phone number'

        if sent:
            reminder.status = 'sent'
            reminder.sent_at = datetime.now(timezone.utc)
            reminder.error_message = None
            db.session.commit()

            logger.info(f"Reminder sent: id={reminder_id}")

            return jsonify({
                'success': True,
                'message': 'Reminder sent successfully',
                'reminder': reminder.to_dict()
            }), 200
        else:
            reminder.status = 'failed'
            reminder.error_message = error_message
            db.session.commit()

            logger.warning(f"Reminder failed to send: id={reminder_id}, error={error_message}")

            return jsonify({
                'success': False,
                'error': error_message or 'Failed to send reminder',
                'reminder': reminder.to_dict()
            }), 500

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error sending reminder: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trip_schedules_bp.route('/process-reminders', methods=['POST'])
def process_pending_reminders():
    """Process all pending reminders (for cron job or task queue)"""
    try:
        now = datetime.now(timezone.utc)
        pending_reminders = Reminder.query.filter(
            Reminder.status == 'pending',
            Reminder.remind_at <= now
        ).all()

        results = {
            'processed': 0,
            'sent': 0,
            'failed': 0,
            'details': []
        }

        for reminder in pending_reminders:
            results['processed'] += 1

            trip_schedule = db.session.get(TripSchedule, reminder.trip_schedule_id)
            if not trip_schedule:
                reminder.status = 'failed'
                reminder.error_message = 'Trip schedule not found'
                results['failed'] += 1
                results['details'].append({
                    'reminder_id': reminder.id,
                    'status': 'failed',
                    'error': 'Trip schedule not found'
                })
                continue

            user = db.session.get(User, trip_schedule.user_id)
            if not user:
                reminder.status = 'failed'
                reminder.error_message = 'User not found'
                results['failed'] += 1
                results['details'].append({
                    'reminder_id': reminder.id,
                    'status': 'failed',
                    'error': 'User not found'
                })
                continue

            # Attempt to send notification
            sent = False
            error_message = None

            if reminder.reminder_type == 'email':
                sent = notification_service.send_trip_reminder_email(user, trip_schedule, reminder)
                if not sent:
                    error_message = 'Failed to send email notification'
            elif reminder.reminder_type == 'sms':
                # TODO: Integrate with SMS provider (e.g., Twilio, Africa's Talking)
                if user.phone_number:
                    logger.info(f"SMS reminder would be sent to {user.phone_number}")
                    sent = True
                else:
                    error_message = 'User does not have a phone number'

            if sent:
                reminder.status = 'sent'
                reminder.sent_at = now
                reminder.error_message = None
                results['sent'] += 1
                results['details'].append({
                    'reminder_id': reminder.id,
                    'status': 'sent'
                })
            else:
                reminder.status = 'failed'
                reminder.error_message = error_message
                results['failed'] += 1
                results['details'].append({
                    'reminder_id': reminder.id,
                    'status': 'failed',
                    'error': error_message
                })

        db.session.commit()

        logger.info(f"Processed {results['processed']} reminders: {results['sent']} sent, {results['failed']} failed")

        return jsonify({
            'success': True,
            'message': f"Processed {results['processed']} reminders",
            'results': results
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing reminders: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
