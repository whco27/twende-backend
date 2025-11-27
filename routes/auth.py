"""Authentication routes for user registration and login"""
from flask import Blueprint, jsonify, request
from models import db, User
import re
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Maximum lengths for database fields
MAX_EMAIL_LENGTH = 255
MAX_NAME_LENGTH = 100
MAX_PHONE_LENGTH = 20


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
                'error': 'User with this email already exists'
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

        db.session.add(new_user)
        db.session.commit()
        logger.info(f"User registered successfully: id={new_user.id}")

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

        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'phone_number' in data:
            user.phone_number = data['phone_number']

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
