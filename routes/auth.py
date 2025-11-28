"""Authentication routes for user registration and login"""
from flask import Blueprint, jsonify, request
from models import db, User
from services.notifications import notification_service
from sqlalchemy.exc import IntegrityError
import re
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Maximum lengths for database fields
MAX_EMAIL_LENGTH = 255
MAX_NAME_LENGTH = 100
MAX_PHONE_LENGTH = 20

# Default pagination settings
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def sanitize_string(value):
    """Sanitize string input by stripping whitespace"""
    if value is None:
        return None
    return str(value).strip()


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength (min 8 characters)"""
    return len(password) >= 8


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json(silent=True)
        logger.info("Registration request received")

        if not data:
            logger.warning("Registration failed: No data provided")
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Sanitize inputs (strip whitespace)
        email = sanitize_string(data.get('email'))
        password = data.get('password', '')  # Don't strip password whitespace
        first_name = sanitize_string(data.get('first_name'))
        last_name = sanitize_string(data.get('last_name'))
        phone_number = sanitize_string(data.get('phone_number'))

        # Validate required fields
        if not email:
            logger.warning("Registration failed: Missing email")
            return jsonify({
                'success': False,
                'error': 'Missing required field: email'
            }), 400
        if not password:
            logger.warning("Registration failed: Missing password")
            return jsonify({
                'success': False,
                'error': 'Missing required field: password'
            }), 400
        if not first_name:
            logger.warning("Registration failed: Missing first_name")
            return jsonify({
                'success': False,
                'error': 'Missing required field: first_name'
            }), 400
        if not last_name:
            logger.warning("Registration failed: Missing last_name")
            return jsonify({
                'success': False,
                'error': 'Missing required field: last_name'
            }), 400

        # Validate email format
        if not validate_email(email):
            logger.warning("Registration failed: Invalid email format")
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400

        # Validate email length
        if len(email) > MAX_EMAIL_LENGTH:
            logger.warning(f"Registration failed: Email too long ({len(email)} characters)")
            return jsonify({
                'success': False,
                'error': f'Email must be {MAX_EMAIL_LENGTH} characters or less'
            }), 400

        # Validate name lengths
        if len(first_name) > MAX_NAME_LENGTH:
            logger.warning(f"Registration failed: First name too long ({len(first_name)} characters)")
            return jsonify({
                'success': False,
                'error': f'First name must be {MAX_NAME_LENGTH} characters or less'
            }), 400
        if len(last_name) > MAX_NAME_LENGTH:
            logger.warning(f"Registration failed: Last name too long ({len(last_name)} characters)")
            return jsonify({
                'success': False,
                'error': f'Last name must be {MAX_NAME_LENGTH} characters or less'
            }), 400

        # Validate phone number length if provided
        if phone_number and len(phone_number) > MAX_PHONE_LENGTH:
            logger.warning(f"Registration failed: Phone number too long ({len(phone_number)} characters)")
            return jsonify({
                'success': False,
                'error': f'Phone number must be {MAX_PHONE_LENGTH} characters or less'
            }), 400

        # Validate password strength
        if not validate_password(password):
            logger.warning("Registration failed: Password too weak")
            return jsonify({
                'success': False,
                'error': 'Password must be at least 8 characters long'
            }), 400

        # Check if user already exists
        logger.debug("Checking for existing user with email")
        existing_user = User.query.filter_by(email=email.lower()).first()
        if existing_user:
            logger.warning("Registration failed: Email already exists")
            return jsonify({
                'success': False,
                'error': 'A user with this email already exists',
                'error_code': 'EMAIL_ALREADY_EXISTS',
                'message': 'This email address is already registered. Please use a different email or try logging in instead.',
                'suggestions': [
                    'Use a different email address',
                    'Try logging in with your existing account',
                    'Use the forgot password feature if you forgot your credentials'
                ]
            }), 409

        # Create new user
        email_domain = email.split('@')[1] if '@' in email else 'unknown'
        logger.debug(f"Creating new user for domain: {email_domain}")
        new_user = User(
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"User registered successfully: id={new_user.id}")
        except IntegrityError:
            # Handle race condition: another request inserted the same email
            # between our check and insert
            db.session.rollback()
            logger.warning(
                f"Registration failed due to duplicate email (race condition): "
                f"{email.lower()}"
            )
            return jsonify({
                'success': False,
                'error': 'This email address is already registered',
                'error_code': 'EMAIL_ALREADY_EXISTS',
                'message': 'Please use a different email address or try logging in.',
                'suggestions': [
                    'Use a different email address',
                    'Try logging in with your existing account'
                ]
            }), 409

        # Send notification emails (non-blocking - failures don't affect registration)
        try:
            notification_service.send_registration_confirmation(new_user)
        except Exception as e:
            logger.warning(
                f"Failed to send registration confirmation email: {str(e)}"
            )

        try:
            notification_service.notify_admin_new_registration(new_user)
        except Exception as e:
            logger.warning(
                f"Failed to send admin notification email: {str(e)}"
            )

        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration failed with exception: {type(e).__name__}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Registration failed. Please try again later.'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return user info"""
    try:
        data = request.get_json(silent=True)
        logger.info("Login request received")

        if not data:
            logger.warning("Login failed: No data provided")
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate required fields
        if 'email' not in data or 'password' not in data:
            logger.warning("Login failed: Missing email or password")
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400

        # Find user
        user = User.query.filter_by(email=data['email'].lower()).first()

        if not user or not user.check_password(data['password']):
            logger.warning("Login failed: Invalid credentials")
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401

        if not user.is_active:
            logger.warning(f"Login failed: Account deactivated for user id={user.id}")
            return jsonify({
                'success': False,
                'error': 'Account is deactivated'
            }), 403

        logger.info(f"User logged in successfully: id={user.id}")
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Login failed with exception: {type(e).__name__}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Login failed. Please try again later.'
        }), 500


@auth_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    try:
        logger.debug(f"Get user request: id={user_id}")
        user = db.session.get(User, user_id)
        if not user:
            logger.warning(f"Get user failed: User not found id={user_id}")
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Get user failed with exception: {type(e).__name__}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve user. Please try again later.'
        }), 500


@auth_bp.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user information"""
    try:
        logger.debug(f"Update user request: id={user_id}")
        user = db.session.get(User, user_id)
        if not user:
            logger.warning(f"Update user failed: User not found id={user_id}")
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        data = request.get_json(silent=True)
        if not data:
            logger.warning("Update user failed: No data provided")
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate name fields if provided (cannot be empty)
        name_fields = ['first_name', 'last_name']
        for field in name_fields:
            if field in data:
                value = sanitize_string(data[field])
                if not value:
                    logger.warning(f"Update user failed: {field} cannot be empty")
                    return jsonify({
                        'success': False,
                        'error': f'{field} cannot be empty'
                    }), 400
                if len(value) > MAX_NAME_LENGTH:
                    logger.warning(f"Update user failed: {field} too long ({len(value)} characters)")
                    return jsonify({
                        'success': False,
                        'error': f'{field} must be {MAX_NAME_LENGTH} characters or less'
                    }), 400

        # Validate phone number length if provided
        if 'phone_number' in data and data['phone_number']:
            phone_number = sanitize_string(data['phone_number'])
            if phone_number and len(phone_number) > MAX_PHONE_LENGTH:
                logger.warning(f"Update user failed: Phone number too long ({len(phone_number)} characters)")
                return jsonify({
                    'success': False,
                    'error': f'Phone number must be {MAX_PHONE_LENGTH} characters or less'
                }), 400

        # Update allowed fields
        if 'first_name' in data:
            user.first_name = sanitize_string(data['first_name'])
        if 'last_name' in data:
            user.last_name = sanitize_string(data['last_name'])
        if 'phone_number' in data:
            user.phone_number = sanitize_string(data['phone_number'])

        db.session.commit()
        logger.info(f"User updated successfully: id={user_id}")

        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update user failed with exception: {type(e).__name__}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to update user. Please try again later.'
        }), 500


@auth_bp.route('/check-email', methods=['POST'])
def check_email_availability():
    """Check if an email is available for registration.

    This endpoint allows clients to pre-validate email availability
    before attempting registration, providing immediate feedback to users.
    """
    try:
        data = request.get_json(silent=True)
        logger.debug("Email availability check request received")

        if not data or 'email' not in data:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400

        email = sanitize_string(data.get('email'))

        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400

        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format',
                'available': False
            }), 400

        # Check if email exists
        existing_user = User.query.filter_by(email=email.lower()).first()

        if existing_user:
            logger.debug(f"Email availability check: {email.lower()} is taken")
            return jsonify({
                'success': True,
                'available': False,
                'message': 'Email is already in use'
            }), 200

        logger.debug(f"Email availability check: {email.lower()} is available")
        return jsonify({
            'success': True,
            'available': True,
            'message': 'Email is available'
        }), 200

    except Exception as e:
        logger.error(
            f"Email availability check failed: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'Failed to check email availability. Please try again later.'
        }), 500


@auth_bp.route('/users', methods=['GET'])
def list_users():
    """List all users with pagination (for admin purposes)"""
    try:
        page = request.args.get('page', DEFAULT_PAGE, type=int)
        per_page = request.args.get('per_page', DEFAULT_PER_PAGE, type=int)
        is_active = request.args.get('is_active', type=str)

        # Validate pagination parameters
        if page < 1:
            page = DEFAULT_PAGE
        if per_page < 1 or per_page > MAX_PER_PAGE:
            per_page = DEFAULT_PER_PAGE

        query = User.query

        # Filter by active status if provided
        if is_active is not None:
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            query = query.filter_by(is_active=is_active_bool)

        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in pagination.items],
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
        logger.error(
            f"Failed to list users: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve users. Please try again later.'
        }), 500
